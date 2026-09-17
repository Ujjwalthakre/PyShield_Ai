import ast

# 1. This is the "target" code we want to analyze.
# Notice how we have a comment and a string that contain the word 'eval', 
# plus an actual dangerous eval() call.
target_code = """
# I promise I won't use eval()
safe_string = "The eval() function is dangerous"
"hii im heree"
eval(user_input)
"""

print("--- RAW AST DUMP ---")
# 2. ast.parse() converts the raw string into an AST object
tree = ast.parse(target_code)

# 3. ast.dump() lets us look at the tree structure
print(ast.dump(tree, indent=4))
print("\n--- VISITOR OUTPUT ---")

# 4. We use the Visitor Pattern. 
# ast.NodeVisitor automatically walks the tree for us.
class SecurityVisitor(ast.NodeVisitor):
    
    # By naming a method 'visit_<NodeType>', Python automatically calls this 
    # method every time it encounters that specific node type in the tree.
    # In Python AST, any function call (like eval(), print(), execute()) is a 'Call' node.
    def visit_Call(self, node: ast.Call):
        # We check if the function being called has a standard name (is an ast.Name node)
        if isinstance(node.func, ast.Name) and node.func.id == "eval":
            function_name = node.func.id
            print(f"[CRITICAL] Dangerous use of eval() detected at line {node.lineno}")
            print(f"Detected a function call: {function_name} at line {node.lineno}")
        
        # We must call generic_visit to continue walking down the tree
        # (in case there are function calls inside this function call!)
        self.generic_visit(node)

# 5. Initialize our visitor and tell it to walk the tree
visitor = SecurityVisitor()
visitor.visit(tree)