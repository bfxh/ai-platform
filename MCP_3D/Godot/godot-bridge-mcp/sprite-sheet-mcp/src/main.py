"""Main entry point for the Sprite Sheet MCP server."""

import json
import sys
import os
import logging

# Add src directory to path for imports
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# Configure logging to stderr
logging.basicConfig(
    level=logging.DEBUG if os.environ.get('SPRITE_MCP_VERBOSE') else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class SpriteSheetMCP:
    """MCP Server for sprite sheet analysis."""
    
    def __init__(self):
        self.tools = self._define_tools()
        # Lazy load modules to avoid import errors at startup
        self._detector = None
        self._grouper = None
        self._normalizer = None
        self._exporter = None
    
    @property
    def detector(self):
        if self._detector is None:
            import detector as det_module
            self._detector = det_module
        return self._detector
    
    @property
    def grouper(self):
        if self._grouper is None:
            import grouper as grp_module
            self._grouper = grp_module
        return self._grouper
    
    @property
    def normalizer(self):
        if self._normalizer is None:
            import normalizer as norm_module
            self._normalizer = norm_module
        return self._normalizer
    
    @property
    def exporter(self):
        if self._exporter is None:
            import exporter as exp_module
            self._exporter = exp_module
        return self._exporter
    
    def _define_tools(self):
        """Define available MCP tools."""
        return [
            {
                "name": "sprite_analyze_sheet",
                "description": "Analyze a spritesheet image and detect frames automatically using alpha channel or background color segmentation. Returns bounding boxes for each detected sprite.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to the spritesheet image (PNG recommended)"
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["auto", "alpha", "bg_color"],
                            "description": "Detection mode: auto (detect best method), alpha (use transparency), bg_color (use background color)"
                        },
                        "bg_color": {
                            "type": "object",
                            "properties": {
                                "r": {"type": "integer", "minimum": 0, "maximum": 255},
                                "g": {"type": "integer", "minimum": 0, "maximum": 255},
                                "b": {"type": "integer", "minimum": 0, "maximum": 255},
                                "tolerance": {"type": "integer", "minimum": 0, "maximum": 255}
                            },
                            "description": "Background color for bg_color mode {r,g,b,tolerance}"
                        },
                        "min_area": {
                            "type": "integer",
                            "description": "Minimum area in pixels to consider a valid frame (filters noise)"
                        },
                        "merge_distance": {
                            "type": "integer",
                            "description": "Maximum distance in pixels to merge nearby components into one frame"
                        }
                    },
                    "required": ["image_path"]
                }
            },
            {
                "name": "sprite_slice_frames",
                "description": "Slice detected frames from a spritesheet and export them as individual PNG files or as atlas data.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to the spritesheet image"
                        },
                        "frames": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "x": {"type": "integer"},
                                    "y": {"type": "integer"},
                                    "w": {"type": "integer"},
                                    "h": {"type": "integer"}
                                }
                            },
                            "description": "Array of frame rectangles from sprite_analyze_sheet"
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "Directory to save sliced frames"
                        },
                        "export_mode": {
                            "type": "string",
                            "enum": ["png_frames", "atlas_json"],
                            "description": "Export mode: png_frames (individual PNGs) or atlas_json (metadata only)"
                        },
                        "naming": {
                            "type": "string",
                            "enum": ["frame_{id}", "row_col"],
                            "description": "Naming convention for exported files"
                        },
                        "padding": {
                            "type": "integer",
                            "description": "Padding to add around each frame"
                        }
                    },
                    "required": ["image_path", "frames", "output_dir"]
                }
            },
            {
                "name": "sprite_group_animations",
                "description": "Group detected frames into animations using spatial clustering (rows/columns) or visual similarity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "frames": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "x": {"type": "integer"},
                                    "y": {"type": "integer"},
                                    "w": {"type": "integer"},
                                    "h": {"type": "integer"}
                                }
                            },
                            "description": "Array of frame rectangles"
                        },
                        "grouping_mode": {
                            "type": "string",
                            "enum": ["rows", "columns", "grid", "spatial_cluster"],
                            "description": "Grouping strategy: rows (group by Y), columns (group by X), grid (detect grid), spatial_cluster (DBSCAN)"
                        },
                        "row_tolerance": {
                            "type": "integer",
                            "description": "Y-axis tolerance for row grouping"
                        },
                        "expected_animations": {
                            "type": "integer",
                            "description": "Expected number of animations (helps clustering)"
                        },
                        "ordering": {
                            "type": "string",
                            "enum": ["x_asc", "y_asc", "id"],
                            "description": "Order frames within each animation"
                        }
                    },
                    "required": ["frames"]
                }
            },
            {
                "name": "sprite_preview_layout",
                "description": "Generate a debug preview image showing detected frames with bounding boxes and labels.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to the spritesheet image"
                        },
                        "frames": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "x": {"type": "integer"},
                                    "y": {"type": "integer"},
                                    "w": {"type": "integer"},
                                    "h": {"type": "integer"}
                                }
                            },
                            "description": "Array of frame rectangles"
                        },
                        "animations": {
                            "type": "object",
                            "description": "Animation groups {name: {frameIds: [...]}} for color coding"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Path to save the preview image"
                        },
                        "show_labels": {
                            "type": "boolean",
                            "description": "Show frame ID labels"
                        },
                        "show_dimensions": {
                            "type": "boolean",
                            "description": "Show frame dimensions"
                        }
                    },
                    "required": ["image_path", "frames", "output_path"]
                }
            },
            {
                "name": "sprite_export_godot_json",
                "description": "Export analyzed spritesheet data as JSON compatible with Godot MCP tools (atlas_batch_create, spriteframes_add_frame, etc.).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source_image": {
                            "type": "string",
                            "description": "Path to the original spritesheet (will be converted to res:// path)"
                        },
                        "frames": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "x": {"type": "integer"},
                                    "y": {"type": "integer"},
                                    "w": {"type": "integer"},
                                    "h": {"type": "integer"}
                                }
                            },
                            "description": "Array of frame rectangles"
                        },
                        "animations": {
                            "type": "object",
                            "description": "Animation groups {name: {frameIds: [...], fps: N, loop: bool}}"
                        },
                        "normalize_size": {
                            "type": "string",
                            "enum": ["none", "max", "median"],
                            "description": "Normalize frame sizes for consistent animation"
                        },
                        "pivot": {
                            "type": "string",
                            "enum": ["center", "bottom_center", "top_left"],
                            "description": "Pivot point for frames"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Path to save JSON file (optional, returns JSON if not specified)"
                        },
                        "godot_texture_path": {
                            "type": "string",
                            "description": "Godot res:// path for the texture (e.g. res://Art/sheet.png)"
                        }
                    },
                    "required": ["source_image", "frames", "animations"]
                }
            },
            # ===== NEW TOOLS =====
            {
                "name": "sprite_remove_background",
                "description": "Remove background color from image and create PNG with transparency. Auto-detects background from corners or uses specified color.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to the source image"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Path to save the result (PNG with transparency)"
                        },
                        "bg_color": {
                            "type": "object",
                            "properties": {
                                "r": {"type": "integer", "minimum": 0, "maximum": 255},
                                "g": {"type": "integer", "minimum": 0, "maximum": 255},
                                "b": {"type": "integer", "minimum": 0, "maximum": 255}
                            },
                            "description": "Background color to remove {r,g,b}. Auto-detected from corners if not specified."
                        },
                        "tolerance": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 255,
                            "description": "Color tolerance for background detection (0-255, default 30)"
                        },
                        "feather": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 10,
                            "description": "Edge feathering/smoothing amount (0-10, default 0)"
                        }
                    },
                    "required": ["image_path", "output_path"]
                }
            },
            {
                "name": "sprite_analyze_grid",
                "description": "Analyze spritesheet using fixed grid parameters (like Godot's hframes/vframes). Use when sprites are arranged in a regular grid.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to the spritesheet image"
                        },
                        "columns": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "Number of columns (hframes)"
                        },
                        "rows": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "Number of rows (vframes)"
                        },
                        "offset_x": {
                            "type": "integer",
                            "description": "X offset from left edge to start (default 0)"
                        },
                        "offset_y": {
                            "type": "integer",
                            "description": "Y offset from top edge to start (default 0)"
                        },
                        "spacing_x": {
                            "type": "integer",
                            "description": "Horizontal spacing between frames (default 0)"
                        },
                        "spacing_y": {
                            "type": "integer",
                            "description": "Vertical spacing between frames (default 0)"
                        },
                        "margin_x": {
                            "type": "integer",
                            "description": "Horizontal margin inside each cell (default 0)"
                        },
                        "margin_y": {
                            "type": "integer",
                            "description": "Vertical margin inside each cell (default 0)"
                        }
                    },
                    "required": ["image_path", "columns", "rows"]
                }
            },
            {
                "name": "sprite_detect_grid",
                "description": "Auto-detect if a spritesheet has a regular grid pattern. Returns suggested grid parameters if detected.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to the spritesheet image"
                        },
                        "min_cell_size": {
                            "type": "integer",
                            "description": "Minimum expected cell size in pixels (default 16)"
                        },
                        "max_cell_size": {
                            "type": "integer",
                            "description": "Maximum expected cell size in pixels (default 512)"
                        }
                    },
                    "required": ["image_path"]
                }
            },
            {
                "name": "sprite_filter_frames",
                "description": "Filter detected frames by size or position constraints. Useful for removing unwanted detections.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "frames": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Array of frame rectangles to filter"
                        },
                        "min_width": {
                            "type": "integer",
                            "description": "Minimum frame width"
                        },
                        "max_width": {
                            "type": "integer",
                            "description": "Maximum frame width"
                        },
                        "min_height": {
                            "type": "integer",
                            "description": "Minimum frame height"
                        },
                        "max_height": {
                            "type": "integer",
                            "description": "Maximum frame height"
                        },
                        "min_area": {
                            "type": "integer",
                            "description": "Minimum frame area (width * height)"
                        },
                        "max_area": {
                            "type": "integer",
                            "description": "Maximum frame area"
                        },
                        "region": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "integer"},
                                "y": {"type": "integer"},
                                "w": {"type": "integer"},
                                "h": {"type": "integer"}
                            },
                            "description": "Only keep frames inside this region {x, y, w, h}"
                        }
                    },
                    "required": ["frames"]
                }
            },
            {
                "name": "sprite_adjust_frames",
                "description": "Adjust frame positions and sizes. Apply offset, expand/shrink, add padding, or make uniform size.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "frames": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Array of frame rectangles to adjust"
                        },
                        "offset_x": {
                            "type": "integer",
                            "description": "Add to all X positions"
                        },
                        "offset_y": {
                            "type": "integer",
                            "description": "Add to all Y positions"
                        },
                        "expand_x": {
                            "type": "integer",
                            "description": "Expand width (negative to shrink)"
                        },
                        "expand_y": {
                            "type": "integer",
                            "description": "Expand height (negative to shrink)"
                        },
                        "padding": {
                            "type": "integer",
                            "description": "Add uniform padding to all sides"
                        },
                        "uniform_size": {
                            "type": "boolean",
                            "description": "Make all frames the same size (use max dimensions)"
                        }
                    },
                    "required": ["frames"]
                }
            },
            {
                "name": "sprite_sample_colors",
                "description": "Sample colors from corners, edges, or specific points of an image. Useful for identifying background color.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to the image"
                        },
                        "sample_points": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "x": {"type": "integer"},
                                    "y": {"type": "integer"}
                                }
                            },
                            "description": "List of {x, y} points to sample"
                        },
                        "sample_corners": {
                            "type": "boolean",
                            "description": "Sample from image corners (default true)"
                        },
                        "sample_edges": {
                            "type": "boolean",
                            "description": "Sample from image edges (default false)"
                        },
                        "sample_count": {
                            "type": "integer",
                            "description": "Number of samples per edge (default 10)"
                        }
                    },
                    "required": ["image_path"]
                }
            }
        ]
    
    def handle_tool_call(self, name, arguments):
        """Handle a tool call."""
        try:
            result = self._execute_tool(name, arguments)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception(f"Tool error: {e}")
            return json.dumps({"error": str(e)})
    
    def _execute_tool(self, name, args):
        """Execute a tool."""
        if name == "sprite_analyze_sheet":
            return self.detector.analyze_sheet(
                image_path=args.get("image_path"),
                mode=args.get("mode", "auto"),
                bg_color=args.get("bg_color"),
                min_area=args.get("min_area", 64),
                merge_distance=args.get("merge_distance", 4)
            )
        
        elif name == "sprite_slice_frames":
            return self.detector.slice_frames(
                image_path=args.get("image_path"),
                frames=args.get("frames", []),
                output_dir=args.get("output_dir"),
                export_mode=args.get("export_mode", "png_frames"),
                naming=args.get("naming", "frame_{id}"),
                padding=args.get("padding", 0)
            )
        
        elif name == "sprite_group_animations":
            return self.grouper.group_animations(
                frames=args.get("frames", []),
                grouping_mode=args.get("grouping_mode", "rows"),
                row_tolerance=args.get("row_tolerance", 10),
                expected_animations=args.get("expected_animations"),
                ordering=args.get("ordering", "x_asc")
            )
        
        elif name == "sprite_preview_layout":
            return self.detector.preview_layout(
                image_path=args.get("image_path"),
                frames=args.get("frames", []),
                animations=args.get("animations"),
                output_path=args.get("output_path"),
                show_labels=args.get("show_labels", True),
                show_dimensions=args.get("show_dimensions", False)
            )
        
        elif name == "sprite_export_godot_json":
            return self.exporter.export_godot_json(
                source_image=args.get("source_image"),
                frames=args.get("frames", []),
                animations=args.get("animations", {}),
                normalize_size=args.get("normalize_size", "none"),
                pivot=args.get("pivot", "center"),
                output_path=args.get("output_path"),
                godot_texture_path=args.get("godot_texture_path")
            )
        
        # ===== NEW TOOL HANDLERS =====
        elif name == "sprite_remove_background":
            return self.detector.remove_background(
                image_path=args.get("image_path"),
                output_path=args.get("output_path"),
                bg_color=args.get("bg_color"),
                tolerance=args.get("tolerance", 30),
                feather=args.get("feather", 0),
                mode=args.get("mode", "color")
            )
        
        elif name == "sprite_analyze_grid":
            return self.detector.analyze_grid(
                image_path=args.get("image_path"),
                columns=args.get("columns"),
                rows=args.get("rows"),
                offset_x=args.get("offset_x", 0),
                offset_y=args.get("offset_y", 0),
                spacing_x=args.get("spacing_x", 0),
                spacing_y=args.get("spacing_y", 0),
                margin_x=args.get("margin_x", 0),
                margin_y=args.get("margin_y", 0)
            )
        
        elif name == "sprite_detect_grid":
            return self.detector.detect_grid(
                image_path=args.get("image_path"),
                min_cell_size=args.get("min_cell_size", 16),
                max_cell_size=args.get("max_cell_size", 512)
            )
        
        elif name == "sprite_filter_frames":
            return self.detector.filter_frames(
                frames=args.get("frames", []),
                min_width=args.get("min_width"),
                max_width=args.get("max_width"),
                min_height=args.get("min_height"),
                max_height=args.get("max_height"),
                min_area=args.get("min_area"),
                max_area=args.get("max_area"),
                region=args.get("region")
            )
        
        elif name == "sprite_adjust_frames":
            return self.detector.adjust_frames(
                frames=args.get("frames", []),
                offset_x=args.get("offset_x", 0),
                offset_y=args.get("offset_y", 0),
                expand_x=args.get("expand_x", 0),
                expand_y=args.get("expand_y", 0),
                padding=args.get("padding", 0),
                uniform_size=args.get("uniform_size", False)
            )
        
        elif name == "sprite_sample_colors":
            return self.detector.sample_colors(
                image_path=args.get("image_path"),
                sample_points=args.get("sample_points"),
                sample_corners=args.get("sample_corners", True),
                sample_edges=args.get("sample_edges", False),
                sample_count=args.get("sample_count", 10)
            )
        
        else:
            raise Exception(f"Unknown tool: {name}")
    
    def send_response(self, msg_id, result):
        """Send JSON-RPC response."""
        response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
        output = json.dumps(response)
        sys.stdout.write(output + "\n")
        sys.stdout.flush()
    
    def send_error(self, msg_id, code, message):
        """Send JSON-RPC error."""
        response = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}
        output = json.dumps(response)
        sys.stdout.write(output + "\n")
        sys.stdout.flush()
    
    def handle_message(self, message):
        """Handle incoming MCP message."""
        method = message.get("method", "")
        msg_id = message.get("id")
        params = message.get("params", {})
        
        logger.debug(f"Received: {method}")
        
        if method == "initialize":
            self.send_response(msg_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "sprite-sheet-mcp", "version": "1.0.0"}
            })
        
        elif method == "notifications/initialized":
            pass  # No response needed for notifications
        
        elif method == "tools/list":
            self.send_response(msg_id, {"tools": self.tools})
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            result = self.handle_tool_call(tool_name, tool_args)
            self.send_response(msg_id, {"content": [{"type": "text", "text": result}]})
        
        elif method == "resources/list":
            self.send_response(msg_id, {"resources": []})
        
        elif method == "prompts/list":
            self.send_response(msg_id, {"prompts": []})
        
        else:
            if msg_id is not None:
                self.send_error(msg_id, -32601, f"Method not found: {method}")
    
    def run(self):
        """Run the MCP server - synchronous stdin reading."""
        logger.info("Sprite Sheet MCP starting...")
        
        # Simple synchronous stdin reading
        for line in sys.stdin:
            try:
                line = line.strip()
                if not line:
                    continue
                
                message = json.loads(line)
                self.handle_message(message)
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON error: {e}")
            except Exception as e:
                logger.exception(f"Error: {e}")


def main():
    server = SpriteSheetMCP()
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
