"""
JavaScript AST Parser using tree-sitter

Extracts functions, classes, and dependencies from JavaScript code.
"""

from tree_sitter import Language, Parser
import tree_sitter_javascript as tsjs
from typing import List, Dict, Any, Set
import logging

logger = logging.getLogger(__name__)


class JavaScriptASTParser:
    """Parse JavaScript code using tree-sitter"""
    
    def __init__(self):
        """Initialize JavaScript parser"""
        try:
            # Create language object
            self.JS_LANGUAGE = Language(tsjs.language())
            
            # Create parser
            self.parser = Parser(self.JS_LANGUAGE)
            
            logger.info("JavaScript parser initialized")
        except Exception as e:
            logger.error(f"Failed to initialize JavaScript parser: {e}")
            raise
    
    def parse_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Parse a JavaScript file
        
        Args:
            file_path: Path to the file
            content: File content
        
        Returns:
            Parsed file data with functions, classes, and dependencies
        """
        try:
            tree = self.parser.parse(bytes(content, "utf8"))
            root_node = tree.root_node
            
            # Extract imports
            imports = self._extract_imports(root_node, content)
            
            # Extract functions
            functions = self._extract_functions(root_node, content)
            
            # Extract classes
            classes = self._extract_classes(root_node, content)
            
            # Extract calls for call graph
            calls = self._extract_calls(root_node, content, functions, classes)
            
            return {
                'file_path': file_path,
                'language': 'javascript',
                'imports': imports,
                'functions': functions,
                'classes': classes,
                'calls': calls
            }
        
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return {'error': str(e)}
    
    def _extract_imports(self, root_node, content: str) -> List[Dict[str, Any]]:
        """Extract import statements"""
        imports = []
        query = self.JS_LANGUAGE.query("""
            (import_statement) @import
        """)
        
        captures = query.captures(root_node)
        for node, _ in captures:
            import_text = self._get_node_text(node, content)
            imports.append({
                'statement': import_text,
                'line': node.start_point[0] + 1
            })
        
        return imports
    
    def _extract_functions(self, root_node, content: str) -> List[Dict[str, Any]]:
        """Extract function definitions"""
        functions = []
        
        # Query for different function types
        query = self.JS_LANGUAGE.query("""
            (function_declaration) @func
            (arrow_function) @arrow
            (function_expression) @func_expr
        """)
        
        captures = query.captures(root_node)
        for node, capture_name in captures:
            func_data = self._extract_function_info(node, content, capture_name)
            if func_data:
                functions.append(func_data)
        
        return functions
    
    def _extract_function_info(self, node, content: str, node_type: str) -> Dict[str, Any]:
        """Extract information from a function node"""
        name = "anonymous"
        
        # Try to get function name
        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child, content)
                break
        
        # Get parameters
        params = []
        for child in node.children:
            if child.type == 'formal_parameters':
                for param in child.children:
                    if param.type == 'identifier':
                        params.append(self._get_node_text(param, content))
        
        # Get function body to extract calls
        calls = []
        dependencies = set()
        for child in node.children:
            if child.type == 'statement_block':
                calls, dependencies = self._extract_function_calls(child, content)
        
        return {
            'name': name,
            'type': 'function',
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'params': params,
            'calls': calls,
            'dependencies': list(dependencies)
        }
    
    def _extract_classes(self, root_node, content: str) -> List[Dict[str, Any]]:
        """Extract class definitions"""
        classes = []
        
        query = self.JS_LANGUAGE.query("""
            (class_declaration) @class
        """)
        
        captures = query.captures(root_node)
        for node, _ in captures:
            class_data = self._extract_class_info(node, content)
            if class_data:
                classes.append(class_data)
        
        return classes
    
    def _extract_class_info(self, node, content: str) -> Dict[str, Any]:
        """Extract information from a class node"""
        name = "anonymous"
        methods = []
        
        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child, content)
            elif child.type == 'class_body':
                # Extract methods
                for method in child.children:
                    if method.type == 'method_definition':
                        method_info = self._extract_method_info(method, content)
                        if method_info:
                            methods.append(method_info['name'])
        
        return {
            'name': name,
            'type': 'class',
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'methods': methods
        }
    
    def _extract_method_info(self, node, content: str) -> Dict[str, Any]:
        """Extract method information"""
        name = "unknown"
        
        for child in node.children:
            if child.type == 'property_identifier':
                name = self._get_node_text(child, content)
        
        return {
            'name': name,
            'type': 'method',
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1
        }
    
    def _extract_function_calls(self, node, content: str) -> tuple:
        """Extract function calls from a node"""
        calls = []
        dependencies = set()
        
        query = self.JS_LANGUAGE.query("""
            (call_expression) @call
        """)
        
        captures = query.captures(node)
        for call_node, _ in captures:
            # Get the function being called
            for child in call_node.children:
                if child.type in ['identifier', 'member_expression']:
                    call_name = self._get_node_text(child, content)
                    calls.append(call_name)
                    
                    # Extract module/object name
                    if '.' in call_name:
                        module = call_name.split('.')[0]
                        dependencies.add(module)
        
        return calls, dependencies
    
    def _extract_calls(
        self, 
        root_node, 
        content: str,
        functions: List[Dict[str, Any]],
        classes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract call relationships for call graph"""
        calls = []
        
        for func in functions:
            for call in func.get('calls', []):
                calls.append({
                    'caller': func['name'],
                    'callee': call,
                    'caller_type': 'function',
                    'line': func['start_line']
                })
        
        return calls
    
    def _get_node_text(self, node, content: str) -> str:
        """Get text content of a node"""
        return content[node.start_byte:node.end_byte]
