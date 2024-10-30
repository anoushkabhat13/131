from brewparse import parse_program     # imports parser
from intbase import InterpreterBase
from intbase import ErrorType

class Interpreter(InterpreterBase):
    
    def __init__(self, console_output=True, inp=None, trace_output=False):
         super().__init__(console_output, inp)   # call InterpreterBase's constructor
   
    def run(self, program):
        ast = parse_program(program)
        self.variable_to_value = {}
      
        #first elem_type should always be a program
        if ast.elem_type != super().PROGRAM_NODE:
            super().output("ERROR")

        #all the functions that the ast has, in this case, we have only 1, so we access the 0th element
        main_func = ast.get("functions")[0]
        
        #need to add check to see if one of the functions is not main
        #better way may be to run each function one at a time by iterating through dict and then checking if at least one has the name main
        #in this case, we have only one function, so it's name must be main
        #super().output(ast)
        #super().output(main_func)
    
        #now we can call on the run_func function and send in the main func
        self.run_func(main_func)
    
    def run_func(self, main):
        for statement_node in main.get("statements"):
            #super().output(type(statement_node))
            #super().output(statement_node)
            #super().output('\n')
            self.run_statement(statement_node)

    def run_statement(self, statement_node):
    
        if(statement_node.elem_type == super().VAR_DEF_NODE):
            self.run_definition(statement_node)

        elif(statement_node.elem_type == super().FCALL_NODE):
            self.run_func_call(statement_node)
        
        elif(statement_node.elem_type == "="):
            self.run_assignment(statement_node)
        
        #super().output(statement_node)
        #super().output(type(statement_node))
        #super().output(statement_node.elem_type)
            
    def run_definition(self, statement_node):
        #super().output(statement_node)
        #super().output(statement_node.get("name"))
        var_name =  statement_node.get("name")

        #if variable has already been defined (already in the dictionary) throw an error
        if var_name in self.variable_to_value:
            super().error(
                ErrorType.NAME_ERROR,
                f"Variable {var_name} defined more than once",
            )
        self.variable_to_value[var_name] = None
        #super().output(self.variable_to_value)

 

    def run_assignment(self, statement_node):
       
        target_variable  = statement_node.get("name") 
        if target_variable not in self.variable_to_value:
            super().error(
                ErrorType.NAME_ERROR,
                f"Variable {target_variable} has not been defined",
            )
        source_node = statement_node.get("expression")
        resulting_value = self.eval_expression(source_node)
        #self.output(target_variable)
        #self.output(resulting_value)
        #self.output(type(resulting_value))
        self.variable_to_value[target_variable] = resulting_value


    def eval_expression(self, expression_node):
        expression_type = expression_node.elem_type
        #super().output(expression_node)
        
        #handles the value node case
        if self.isValue(expression_node): 
            return self.getValue(expression_node)
        
        #handles the variable case
        elif self.isVariable(expression_node):
            return self.getVariable(expression_node)

        #handles the binary operator case
        elif self.isBinaryOperator(expression_node):
            return self.evaluate_binary_operator(expression_node)
        
        #handles function call
        else:
            return self.run_func_call(expression_node)

        
 
    
    def isValue(self, node):
        if node.elem_type == "int" or node.elem_type == "string":
            return True
        return False
    
    def getValue(self, node):
        return node.get("val")
    
    def isVariable(self, node):
        if node.elem_type == "var":
            return True
        return False

    def getVariable(self, node):
        return self.variable_to_value[node.get("name")]

    def isBinaryOperator(self,node):
        if node.elem_type == "-" or node.elem_type == "+":
            return True
        return False

    
    def evaluate_binary_operator(self, expression_node):
        #self.output("HI")
        #self.output(expression_node)
        #self.output(expression_node.get("op1"))

        op1 = self.eval_expression(expression_node.get("op1"))
        op2 = self.eval_expression(expression_node.get("op2"))
        #op1 = self.evaluate_op(expression_node.get("op1"))
        #op2 = self.evaluate_op(expression_node.get("op2"))
        
        #self.output(type(op1))
        #self.output(type(op2))

        
        if not isinstance(op1, int) or not isinstance(op2,int):
            super().error(
             ErrorType.TYPE_ERROR,
            "Incompatible types for arithmetic operation",
        )
        if expression_node.elem_type == "+":
            return op1 + op2
        else:
            return op1 - op2

    """
    def evaluate_op(self,operation):
        if self.isValue(operation):
            return self.getValue(operation)
        elif self.isVariable(operation):
            return self.getVariable(operation)
        else: 
            return self.eval_expression(operation)
    """

        
        
    
    def run_func_call(self, func_node):
    
        func_name = func_node.get("name")
        #super().output(func_name)
        if func_name == "print":
            string_to_output = ""
            for i in func_node.get("args"): 
                if  i.elem_type == "string": 
                    string_to_output += i.get("val")
                else:
                    string_to_output+= str(self.eval_expression(i))
                """
                elif self.isVariable(i):
                    string_to_output += str(self.getVariable(i))
                elif self.isValue(i):
                    string_to_output +=str(self.getValue(i))
                else self.isBinaryOperator(self,node):
                    string_to_output+= str(self.eval_expression(i))
                """
            return super().output(string_to_output)
            
                
        elif func_name == "inputi":
            if func_node.get("args"):
                a = func_node.get("args")[0].get("val")
                super().output(a)
            
            user_input = super().get_input()
           
            try:
                return int(user_input)
            except: 
                return user_input

        else:
            super().error(
                    ErrorType.NAME_ERROR,
                    f"Function {func_name} has not been defined",
            )




interpreter = Interpreter()
program_source = """func main() {
    var foo;
    var bar;
    foo = 2;
    bar = 3;
    print(foo - (bar + inputi("give me something: ")));
}
"""
interpreter.run(program_source)

