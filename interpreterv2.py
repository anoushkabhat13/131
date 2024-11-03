# Add to spec:
# - printing out a nil value is undefined

from env_v1 import EnvironmentManager
from type_valuev1 import Type, Value, create_value, get_printable
from intbase import InterpreterBase, ErrorType
from brewparse import parse_program


# Main interpreter class
class Interpreter(InterpreterBase):
    # constants
    BIN_COMP_OPS = {"+", "-", "*", "/", "||", "&&",  "==", "!=", "<", "<=", ">", ">="}
    UNARY_OPS = {"neg", "!"}
    # methods
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.__setup_ops()

    # run a program that's provided in a string
    # use the provided Parser found in brewparse.py to parse the program
    # into an abstract syntax tree (ast)
    def run(self, program):
        ast = parse_program(program)
        self.__set_up_function_table(ast)
        main_func = self.__get_func_by_name("main")[0]
        self.env = EnvironmentManager()
        self.__run_statements(main_func.get("statements"))

    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}
        for func_def in ast.get("functions"):
            func_name = func_def.get("name")
             # Initialize the dictionary if the function name is not in the table
            if func_name not in self.func_name_to_ast:
                 self.func_name_to_ast[func_name] = {}

            self.func_name_to_ast[func_name][len(func_def.get("args"))] = func_def

    def __get_func_by_name(self, name):
        if name not in self.func_name_to_ast:
            super().error(ErrorType.NAME_ERROR, f"Function {name} not found")
        return self.func_name_to_ast[name]

    def __run_statements(self, statements):
        # all statements of a function are held in arg3 of the function AST node
        for statement in statements:
            if self.trace_output:
                print(statement)
            if statement.elem_type == InterpreterBase.FCALL_NODE:
                self.__call_func(statement)
            elif statement.elem_type == "=":
                self.__assign(statement)
            elif statement.elem_type == InterpreterBase.VAR_DEF_NODE:
                self.__var_def(statement)
            elif statement.elem_type == InterpreterBase.IF_NODE:
                return_val = self.__if(statement)
                if return_val is not None:
                    return return_val
            elif statement.elem_type == InterpreterBase.FOR_NODE:
                return_val = self.__for(statement)
                if return_val is not None:
                    return return_val
            elif statement.elem_type == InterpreterBase.RETURN_NODE:
                return self.__return(statement)
            
            
            
                

    #if statement
    #add scoping to remove and add_scope when if and else statements are entered
    def __if(self, if_ast):
        condition = if_ast.get("condition")
        result = None
        output = self.__eval_expr(condition).value()
        if not isinstance(output, bool):
            super().error(ErrorType.TYPE_ERROR, "Condition must evaluate to bool")

        if (output == True):
            self.env.add_scope("if")
            #super().output("HERE0")
            #super().output("HERE0I")
            result = self.__run_statements(if_ast.get("statements"))
            #super().output("HERE0I")
            #super().output(result)
            self.env.remove_scope("if")
        elif(output == False and if_ast.get("else_statements")!= None):
            self.env.add_scope("if")
            result = self.__run_statements(if_ast.get("else_statements"))
            self.env.remove_scope("if")
        return result
 
    #need to fix for scoping
    def __for(self, for_ast):
        self.__assign(for_ast.get("init")) 
        self.env.add_scope("for")
        result = None

        output = self.__eval_expr(for_ast.get("condition")).value() 
        if not isinstance(output, bool):
            super().error(ErrorType.TYPE_ERROR, "Condition must evaluate to bool")

        while (self.__eval_expr(for_ast.get("condition")).value() == True):
            result = self.__run_statements(for_ast.get("statements"))
            if result is not None:  # If there is a return value, propagate it
                break
            self.__assign(for_ast.get("update"))
        self.env.remove_scope("for")

        return result


    def __return(self, return_ast):
        #super().output(return_ast)
        returnVal = Value(Type.NIL, None)
        if return_ast.get("expression") is not None:
            #super().output("HERE")
            #super().output(return_ast.get("expression"))
            returnVal = self.__eval_expr(return_ast.get("expression"))
            #super().output(returnVal)
            #super().output(returnVal.type())
        return returnVal


    def __call_func(self, call_node):
        func_name = call_node.get("name")
        if func_name == "print":
            return self.__call_print(call_node)
        if func_name == "inputi":
            return self.__call_input(call_node)
        if func_name == "inputs":
            return self.__call_inputs(call_node)
        
        # add code here later to call other functions
        if func_name in self.func_name_to_ast:
            args = [self.__eval_expr(arg) for arg in call_node.get('args')]
            num_args = len(args)
            if num_args in self.func_name_to_ast[func_name]:
                func_def = self.func_name_to_ast[func_name][num_args]
                variables = func_def.get('args') # variables from func definition
                #args = call_node.get('args')    #args/params passed in
                
                #basically we need to set each arg of call_node to func_def
                #evaluate args
                #length of args 
                
                # Evaluate the arguments
                self.env.add_scope("func")
                for variable, value in zip(variables, args):
                    self.env.create(variable.get("name"), Value(Type.NIL, None))
                    self.env.set(variable.get("name"), value)

                result = self.__run_statements(func_def.get("statements"))
                #super().output(result)
                self.env.remove_scope("func")
                
                if result is not None:  # If there's a return value, pass it back
                    return result
                return Value(Type.NIL, None)
            super().error(ErrorType.NAME_ERROR, f"Wrong number of inputs to {func_name}")
        super().error(ErrorType.NAME_ERROR, f"Function {func_name} not found")

    def __call_print(self, call_ast):
        output = ""
        for arg in call_ast.get("args"):
            result = self.__eval_expr(arg)  # result is a Value object
            output = output + get_printable(result)
        super().output(output)

    def __call_input(self, call_ast):
        args = call_ast.get("args")
        if args is not None and len(args) == 1:
            result = self.__eval_expr(args[0])
            super().output(get_printable(result))
        elif args is not None and len(args) > 1:
            super().error(
                ErrorType.NAME_ERROR, "No inputi() function that takes > 1 parameter"
            )
        inp = super().get_input()
        if call_ast.get("name") == "inputi":
            return Value(Type.INT, int(inp))
        # we can support inputs here later

    def __call_inputs(self, call_ast):
        args = call_ast.get("args")
        if args is not None and len(args) == 1:
            result = self.__eval_expr(args[0])
            super().output(get_printable(result))
        elif args is not None and len(args) > 1:
            super().error(
                ErrorType.NAME_ERROR, "No inputs() function that takes > 1 parameter"
            )
        inp = super().get_input()
        if call_ast.get("name") == "inputs":
            return Value(Type.STRING, str(inp))
        # we can support inputs here later

    
    def __assign(self, assign_ast):
        var_name = assign_ast.get("name")
        value_obj = self.__eval_expr(assign_ast.get("expression"))

        if not self.env.set(var_name, value_obj):
            super().error(
                ErrorType.NAME_ERROR, f"Undefined variable {var_name} in assignment"
            )

    def __var_def(self, var_ast):
        var_name = var_ast.get("name")
        if not self.env.create(var_name, Value(Type.INT, 0)):
            super().error(
                ErrorType.NAME_ERROR, f"Duplicate definition for variable {var_name}"
            )
    
  
    def __eval_expr(self, expr_ast):
        #value case: int
        #super().output("expr_type")
        #super().output(expr_ast)
        
        if expr_ast.elem_type == InterpreterBase.INT_NODE:
            return Value(Type.INT, expr_ast.get("val"))
        #value case: string
        if expr_ast.elem_type == InterpreterBase.STRING_NODE:
            return Value(Type.STRING, expr_ast.get("val"))
        #value case: BOOL
        if expr_ast.elem_type == InterpreterBase.BOOL_NODE:
            #super().output("BOOL NODE")
            return Value(Type.BOOL, expr_ast.get("val"))
        #value case: NIL
        if expr_ast.elem_type == InterpreterBase.NIL_NODE:
            #super().output("GOING HERE")
            #super().output("NIL NODE")
            return Value(Type.NIL, None)
        #var node case
        if expr_ast.elem_type == InterpreterBase.VAR_NODE:
            var_name = expr_ast.get("name")
            val = self.env.get(var_name)
            #super().output("VAL")
            #super().output(val)

            if val is None:
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
            return val
        
        #function call case 
        if expr_ast.elem_type == InterpreterBase.FCALL_NODE:
            return self.__call_func(expr_ast)
        
        #binary operation
        if expr_ast.elem_type in Interpreter.BIN_COMP_OPS:
            return self.__eval_op(expr_ast)
        
        #unary operation
        if expr_ast.elem_type in Interpreter.UNARY_OPS:
            return self.__eval_unary_op(expr_ast)
        """
        if expr_ast.elem_type in InterpreterBase.NEG_NODE:
        """

    def __eval_unary_op(self, expr_ast):
        operand_value = self.__eval_expr(expr_ast.get("op1"))  

        if expr_ast.elem_type == InterpreterBase.NOT_NODE:  
            if operand_value.type() != Type.BOOL:
                super().error(ErrorType.TYPE_ERROR, "Logical NOT must be applied to booleans")
            return Value(Type.BOOL, not operand_value.value())

        if expr_ast.elem_type == InterpreterBase.NEG_NODE:  
            if operand_value.type() != Type.INT:
                super().error(ErrorType.TYPE_ERROR, "Arithmetic negation must be applied to ints")
            return Value(Type.INT, -operand_value.value())

    def __eval_op(self, arith_ast):
        left_value_obj = self.__eval_expr(arith_ast.get("op1"))

        right_value_obj = self.__eval_expr(arith_ast.get("op2"))
        
        if (arith_ast.elem_type != ("==" or "!=")) and left_value_obj.type() != right_value_obj.type():
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible types for {arith_ast.elem_type} operation",
            )

        if arith_ast.elem_type not in (self.op_to_lambda) and arith_ast.elem_type not in (self.op_to_lambda[left_value_obj.type()]):
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible operator {arith_ast.elem_type} for type {left_value_obj.type()}",
            )
        
        if arith_ast.elem_type == "=="  or arith_ast.elem_type == "!=" :
           f = self.op_to_lambda[arith_ast.elem_type]
        else:
            f = self.op_to_lambda[left_value_obj.type()][arith_ast.elem_type]
        return f(left_value_obj, right_value_obj)

    def __setup_ops(self):
        self.op_to_lambda = {}
        # set up operations on integers
        self.op_to_lambda[Type.INT] = {}
        self.op_to_lambda[Type.INT]["+"] = lambda x, y: Value(
            Type.INT, x.value() + y.value()
        )
        self.op_to_lambda[Type.INT]["-"] = lambda x, y: Value(
            Type.INT, x.value() - y.value()
        )
        self.op_to_lambda[Type.INT]["*"] = lambda x, y: Value(
            Type.INT, x.value() * y.value()
        )
        self.op_to_lambda[Type.INT]["/"] = lambda x, y: Value(
            Type.INT, x.value() // y.value()
        )
        self.op_to_lambda[Type.INT][">"] = lambda x, y: Value(
            Type.BOOL, x.value() > y.value()
        )
        self.op_to_lambda[Type.INT]["<"] = lambda x, y: Value(
            Type.BOOL, x.value() < y.value()
        )
        self.op_to_lambda[Type.INT][">="] = lambda x, y: Value(
            Type.BOOL, x.value() >= y.value()
        )
        self.op_to_lambda[Type.INT]["<="] = lambda x, y: Value(
            Type.BOOL, x.value() <= y.value()
        )
      
        
        # add other operators here later for int, string, bool, etc
        # string operations
        self.op_to_lambda[Type.STRING] = {}
        self.op_to_lambda[Type.STRING]["+"] = lambda x, y: Value(
            Type.STRING, x.value() + y.value()
        )
       
        #bool operations
        self.op_to_lambda[Type.BOOL] = {}
        self.op_to_lambda[Type.BOOL]["||"] = lambda x, y: Value(
            Type.BOOL, x.value() or y.value()
        )
        self.op_to_lambda[Type.BOOL]["&&"] = lambda x, y: Value(
            Type.BOOL, x.value() and y.value()
        )

        #"==" and "!=" should work for everything
        self.op_to_lambda["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )
       
    

interpreter = Interpreter()


program_source = """
func foo(a) {
  if (a != 1) {
    if (a != 2) {
      var i;
      for (i = 0; i < 15; i = i + 1) {
        if (i == a) {
          return "oh";
        }
      }
    }
  }
}

func loop1() {
  return loop2();
}
func loop2() {
  return loop3();
}

func loop3() {
  return 5;
}

func main() {
  var a;
  a = 10;
  
  print(foo(a));
  print(loop1());
}
"""
interpreter.run(program_source)

