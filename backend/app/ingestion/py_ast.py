"""
Python AST Parser - Extract functions, classes, and dependencies

Uses Python's built-in AST module to parse code structure.
"""

import ast
from typing import List, Dict, Any, Set
import logging

logger = logging.getLogger(__name__)


class PythonASTParser:
    """Parse Python code using AST"""
    
    def parse_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Parse a Python file
        
        Args:
            file_path: Path to the file
            content: File content
        
        Returns:
            Parsed file data with functions, classes, and dependencies
        """
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return {'error': str(e)}
        
        visitor = PythonVisitor(file_path)
        visitor.visit(tree)
        
        return {
            'file_path': file_path,
            'language': 'python',
            'imports': visitor.imports,
            'functions': visitor.functions,
            'classes': visitor.classes,
            'calls': visitor.calls
        }


class PythonVisitor(ast.NodeVisitor):
    """AST visitor to extract code structure"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports = []
        self.functions = []
        self.classes = []
        self.calls = []
        self.current_class = None
    
    def visit_Import(self, node: ast.Import):
        """Visit import statement"""
        for alias in node.names:
            self.imports.append({
                'module': alias.name,
                'alias': alias.asname
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from...import statement"""
        for alias in node.names:
            self.imports.append({
                'module': f"{node.module}.{alias.name}" if node.module else alias.name,
                'alias': alias.asname
            })
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition"""
        func_data = {
            'name': node.name,
            'type': 'method' if self.current_class else 'function',
            'class_name': self.current_class,
            'start_line': node.lineno,
            'end_line': node.end_lineno,
            'docstring': ast.get_docstring(node),
            'params': [arg.arg for arg in node.args.args],
            'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list],
            'calls': [],
            'dependencies': set()
        }
        
        # Extract function calls within this function
        call_visitor = CallVisitor()
        call_visitor.visit(node)
        func_data['calls'] = call_visitor.calls
        func_data['dependencies'] = list(call_visitor.dependencies)
        
        self.functions.append(func_data)
        
        # Record calls for call graph
        for call in call_visitor.calls:
            self.calls.append({
                'caller': node.name,
                'callee': call,
                'caller_type': 'method' if self.current_class else 'function',
                'line': node.lineno
            })
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition"""
        self.visit_FunctionDef(node)  # Treat same as regular function
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition"""
        previous_class = self.current_class
        self.current_class = node.name
        
        class_data = {
            'name': node.name,
            'type': 'class',
            'start_line': node.lineno,
            'end_line': node.end_lineno,
            'docstring': ast.get_docstring(node),
            'bases': [self._get_name(base) for base in node.bases],
            'methods': [],
            'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list]
        }
        
        self.classes.append(class_data)
        self.generic_visit(node)
        
        self.current_class = previous_class
    
    def _get_decorator_name(self, node) -> str:
        """Get decorator name"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return ''
    
    def _get_name(self, node) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return ''


class CallVisitor(ast.NodeVisitor):
    """Visitor to extract function calls"""
    
    def __init__(self):
        self.calls = []
        self.dependencies = set()
    
    def visit_Call(self, node: ast.Call):
        """Visit function call"""
        call_name = self._get_call_name(node.func)
        if call_name:
            self.calls.append(call_name)
            
            # Extract module/class from call
            if '.' in call_name:
                module = call_name.split('.')[0]
                self.dependencies.add(module)
        
        self.generic_visit(node)
    
    def _get_call_name(self, node) -> str:
        """Get function call name"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_call_name(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        return ''
