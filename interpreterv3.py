# document that we won't have a return inside the init/update of a for loop

import copy
from enum import Enum

from brewparse import parse_program
from env_v2 import EnvironmentManager
from intbase import InterpreterBase, ErrorType
from type_valuev2 import Type, Value, create_value, get_printable


class ExecStatus(Enum):
    CONTINUE = 1
    RETURN = 2


# Main interpreter class
class Interpreter(InterpreterBase):
    # constants
    NIL_VALUE = create_value(InterpreterBase.NIL_DEF)
    TRUE_VALUE = create_value(InterpreterBase.TRUE_DEF)
    BIN_OPS = {"+", "-", "*", "/", "==", "!=", ">", ">=", "<", "<=", "||", "&&"}

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
        self.structs = {}
        self.func_name_to_ast = {}
        self.type_of_struct_dict = {}
        #add a struct table
        self.__set_up_struct_table(ast)
        self.__set_up_function_table(ast)
        self.env = EnvironmentManager(interpreter)
        self.__call_func_aux("main", [])
        self.structs = {}
        self.func_name_to_ast = {}
        self.type_of_struct_dict = {}

    #STRUCT DICT WHICH ONLY STORES NAMES OF STRUCTS
    #Need to also store the variables inside the struct 
    def __set_up_struct_table(self,ast):
        
        for struct_def in ast.get("structs"):
            struct_name = struct_def.get("name")
            struct_fields = struct_def.get("fields")
            if struct_name not in self.structs:
                self.structs[struct_name] = self.__create_class(struct_name, struct_fields, self.structs)

    def __create_class(self, struct_name, struct_fields, structs):
        def __init__(self, **kwargs):
            for field in struct_fields:
                var_name = field.get("name")
                var_type = field.get("var_type")                 
                if var_type == Interpreter.BOOL_NODE:
                    obj_value = create_value(InterpreterBase.FALSE_DEF)
                elif var_type == Interpreter.INT_NODE:
                    obj_value = create_value(0)
                elif var_type  == Interpreter.STRING_NODE:
                    obj_value = create_value("")
                #EDITED THIS
                elif var_type in structs:
                    #create struct 
                    #set to nil initially
                    obj_value = create_value(InterpreterBase.NIL_DEF)
                setattr(self, var_name, obj_value)
                

        def get_type(self):
            return struct_name
        
        # Create a dictionary of methods (including __init__) for the new class
        methods = {'__init__': __init__,'type': get_type}

        # Define the new class using type()
        return type(struct_name, (object,), methods)

    def __set_up_function_table(self, ast):

        
        for func_def in ast.get("functions"):
            func_name = func_def.get("name")
            num_params = len(func_def.get("args"))
            
            for param in func_def.get("args"):
                #print("PARAM")
                #print(param.get("var_type"))
                
                if (param.get("var_type") not in ["bool", "string", "int", "nil"]) and (param.get("var_type") not in self.structs):
                    param_name = param.get("name")
                    super().error(
                        ErrorType.TYPE_ERROR,
                        f"Invalid type for formal parameter {param_name} in function {func_name}",
                    )

            if func_name not in self.func_name_to_ast:
                self.func_name_to_ast[func_name] = {}
             
            self.func_name_to_ast[func_name][num_params] = func_def

    def __get_func_by_name(self, name, num_params):
        if name not in self.func_name_to_ast:
            super().error(ErrorType.NAME_ERROR, f"Function {name} not found")
        candidate_funcs = self.func_name_to_ast[name]
        if num_params not in candidate_funcs:
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {name} taking {num_params} params not found",
            )
        return candidate_funcs[num_params]

    def __run_statements(self, statements):
        self.env.push_block()
        for statement in statements:
            #remove after
            if self.trace_output:
                print(statement)
            status, return_val = self.__run_statement(statement)
            if status == ExecStatus.RETURN:
                self.env.pop_block()
                return (status, return_val)

        self.env.pop_block()
        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __run_statement(self, statement):
        status = ExecStatus.CONTINUE
        return_val = None
        if statement.elem_type == InterpreterBase.FCALL_NODE:
            self.__call_func(statement)
        elif statement.elem_type == "=":
            self.__assign(statement)
        elif statement.elem_type == InterpreterBase.VAR_DEF_NODE:
            self.__var_def(statement)
        elif statement.elem_type == InterpreterBase.RETURN_NODE:
            status, return_val = self.__do_return(statement)
        elif statement.elem_type == Interpreter.IF_NODE:
            status, return_val = self.__do_if(statement)
        elif statement.elem_type == Interpreter.FOR_NODE:
            status, return_val = self.__do_for(statement)
        return (status, return_val)
    
    def __call_func(self, call_node):
        func_name = call_node.get("name")
        actual_args = call_node.get("args")
        return self.__call_func_aux(func_name, actual_args)

    def __call_func_aux(self, func_name, actual_args):

        if func_name == "print":
            return self.__call_print(actual_args)
        if func_name == "inputi" or func_name == "inputs":
            return self.__call_input(func_name, actual_args)

        func_ast = self.__get_func_by_name(func_name, len(actual_args))
        formal_args = func_ast.get("args")

        if len(actual_args) != len(formal_args):
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {func_ast.get('name')} with {len(actual_args)} args not found",
            )

        # first evaluate all of the actual parameters and associate them with the formal parameter names
        args = {}
        for formal_ast, actual_ast in zip(formal_args, actual_args):
            arg_name = formal_ast.get("name")
            arg_type = formal_ast.get("var_type")
            #print(arg_name)
            #print(arg_type)
            #print(actual_ast)
            accepted_types = ["int", "string", "bool", "void"]

            
            if (arg_type not in accepted_types) and (arg_type not in self.structs):
                super().error(
                ErrorType.NAME_ERROR,
                f"Invalid type for formal parameter {arg_name} in function {func_name}*/",
                )

            #print(actual_ast.get_type())
            
            # don't know how to fix
          
            #changing to object reference if struct
            #and arg_type == self.type_of_struct_dict[actual_ast.get("name")]
            if arg_type in self.structs :
                if actual_ast == "nil":
                    result = self.__eval_expr(actual_ast)
                elif actual_ast.get("var_type")!= None and actual_ast.get("var_type")==arg_type:
                    result = self.__eval_expr(actual_ast)
                elif arg_type == self.type_of_struct_dict[actual_ast.get("name")]:
                    result = self.__eval_expr(actual_ast) 
                
                else:
                    super().error(
                        ErrorType.TYPE_ERROR,
                        f"Formal parameter {arg_name} excepted struct of type {arg_type}, type mismatch*/",
                        )
                
               
                #print("HERE")
                #print(result)
                #print(result)
            
            else:
                result = copy.copy(self.__eval_expr(actual_ast))

           
            #bool parameter set to int
            if arg_type == "bool" and result.type() == "int":
                if result.value() == 0:
                    args[arg_name] = Value(Type.BOOL, False)
                else:
                    args[arg_name] = Value(Type.BOOL, True)

            elif arg_type in self.structs and result.type() == "nil":
                args[arg_name] = result

            elif arg_type != result.type():
                super().error(
                ErrorType.TYPE_ERROR,
                f"Wrong type for parameter input",
                )

            else:
                args[arg_name] = result

        # then create the new activation record 
        self.env.push_func()
        # and add the formal arguments to the activation record
        for arg_name, value in args.items():
          self.env.create(arg_name, value)
        _, return_val = self.__run_statements(func_ast.get("statements"))
        self.env.pop_func()

        func_return_type = func_ast.get("return_type")
     
        #int function with nil return type
        if return_val.type() == "nil" and func_return_type == "int":
            return Value(Type.INT,0)
        
        #string function with nil return type
        elif return_val.type() == "nil" and func_return_type == "string":
            return Value(Type.STRING,"")
        
        #bool function with nil return type
        elif return_val.type() == "nil" and func_return_type == "bool":
            return Value(Type.BOOL, False)

        #void function with nil return type
        elif return_val.type()== "nil" and func_return_type == "void":
            return  Value(Type.VOID, None)
        
        #bool return set to int coercion
        elif func_return_type == "bool" and return_val.type() == "int":
            if return_val.value() == 0:
                return Value(Type.BOOL, False)
            else:
                return Value(Type.BOOL, True)
       
         
        elif (func_return_type in self.structs) and return_val.type() == "nil":
            return Value(Type.NIL, None)
        
        elif func_return_type != return_val.type():
                super().error(
                ErrorType.TYPE_ERROR,
                f"The function is supposed to return a {func_return_type} but instead returns a {return_val.type()}",
                )
       
        #print("RETURN VAL")
        #print(return_val)
        return return_val

    def __call_print(self, args):
       
        output = ""
        for arg in args:
            result = self.__eval_expr(arg)  # result is a Value object
            output = output + get_printable(result)
        super().output(output)
        return Interpreter.VOID_DEF

    def __call_input(self, name, args):
        if args is not None and len(args) == 1:
            result = self.__eval_expr(args[0])
            super().output(get_printable(result))
        elif args is not None and len(args) > 1:
            super().error(
                ErrorType.NAME_ERROR, "No inputi() function that takes > 1 parameter"
            )
        inp = super().get_input()
        if name == "inputi":
            return Value(Type.INT, int(inp))
        if name == "inputs":
            return Value(Type.STRING, inp)

    def __assign(self, assign_ast):
       
        var_name = assign_ast.get("name")
        value_obj = self.__eval_expr(assign_ast.get("expression"))
        if "." in var_name:
            self.set_nested_field(var_name, value_obj)
        else:
            if not self.env.set(var_name, value_obj):
                super().error(
                    ErrorType.NAME_ERROR, f"Undefined variable {var_name} in assignment"
                )
    
        """   
        elif var_type!= "":
            super().error(
                    ErrorType.TYPE_ERROR,
                    "NOT FOUND IN VALID STRUCTS",
                )
        """ 
    def __var_def(self, var_ast):
        var_name = var_ast.get("name")
        #retrieve variable type
        var_type = var_ast.get("var_type")
        #set to the default value for that type
        if var_type == Interpreter.BOOL_NODE:
            value = create_value(InterpreterBase.FALSE_DEF)
        elif var_type == Interpreter.INT_NODE:
            value = create_value(0)
        elif var_type  == Interpreter.STRING_NODE:
            value = create_value("")
        #EDITED THIS
        elif var_type in self.structs:
            #create struct 
            #set to nil initially
            value = create_value(InterpreterBase.NIL_DEF)
            self.type_of_struct_dict[var_name] = var_type
      
        else:
            super().error(
                ErrorType.TYPE_ERROR, f"All variable definitions must now specify an explicit type for the variable"
            )
        if not self.env.create(var_name, value):
            super().error(
                ErrorType.NAME_ERROR, f"Duplicate definition for variable {var_name}"
            )

    def set_nested_field(self, var_name, value):
        # Split var_name into parts by dots
        parts = var_name.split('.')
      
        # Start with the top-level object in the environment
        current_obj = self.env.get(parts[0])
        
        if current_obj!= None and current_obj.type() == "nil":
            super().error(
                ErrorType.FAULT_ERROR, f"Dot operator invalid on uninitialized struct"
            )

        if (current_obj == None or current_obj.type() not in self.structs):
            super().error(
                ErrorType.TYPE_ERROR, f"Dot operator only valid on struct"
            )
        

        # Traverse each part except the last to reach the second-to-last object
        for part in parts[1:-1]:
            if current_obj!=None and current_obj.type() == "nil":
                super().error(
                    ErrorType.FAULT_ERROR,  f"Dot operator invalid on uninitialized struct"
                )

            if(current_obj == None or current_obj.type() not in self.structs):
                super().error(
                    ErrorType.TYPE_ERROR, f"Dot operator only valid on struct"
                )

            if not hasattr(current_obj, part):
                super().error(
                    ErrorType.NAME_ERROR, f"Invalid attribute {part}"
                )

            current_obj = getattr(current_obj, part)
           
        if not hasattr(current_obj, parts[-1]):
            super().error(
                ErrorType.NAME_ERROR, f"Invalid attribute {parts[-1]}"
            )

        
        cur_type = getattr(current_obj, parts[-1]).type()
        val_type = value.type()

        if(cur_type == "nil" and val_type in self.structs):
            setattr(current_obj, parts[-1], value)

        elif(cur_type == "bool" and val_type == "int"):
            if value.value() == 0:
                setattr(current_obj, parts[-1], Value(Type.BOOL, False))
            else:
                setattr(current_obj, parts[-1], Value(Type.BOOL, True))
        
        elif(cur_type != val_type):
            super().error(
                    ErrorType.TYPE_ERROR, f"Setting a struct field of type {cur_type} to a value of type {val_type}"
                )
        # Use setattr on the last object to set the final attribute
        else:
             setattr(current_obj, parts[-1], value)


    def get_nested_field(self, var_name):
        # Split var_name into parts by dots (e.g., 'struct1.struct2.field' -> ['struct1', 'struct2', 'field'])
        parts = var_name.split('.')
        
        # Start from the environment dictionary
        current_obj = self.env.get(parts[0])
        

        if current_obj!= None and current_obj.type() == "nil":
            super().error(
                ErrorType.FAULT_ERROR,  f"Dot operator invalid on uninitialized struct"
            )
        
        if(current_obj ==None or current_obj.type() not in self.structs):
            super().error(
                ErrorType.TYPE_ERROR, f"Dot operator only valid on struct"
            )

        # Traverse each part to go deeper
        for part in parts[1:]:
            
            if current_obj!= None and current_obj.type() == "nil":
                super().error(
                    ErrorType.FAULT_ERROR,  f"Dot operator invalid on uninitialized struct"
                )
            
            if(current_obj.type() not in self.structs or current_obj.type() == None):
                super().error(
                    ErrorType.TYPE_ERROR, f"Dot operator only valid on struct"
                )

            if not hasattr(current_obj, part):
                super().error(
                    ErrorType.NAME_ERROR, f"Invalid attribute {part}"
                )
            
            current_obj = getattr(current_obj, part)
            
        
        # Return the final field
        return current_obj
        

    def __eval_expr(self, expr_ast):

        var_name = expr_ast.get("name")
       
        
        if expr_ast.elem_type == InterpreterBase.NEW_NODE:
            struct_name = expr_ast.get("var_type")
            return self.structs[struct_name]()
    
        
        if expr_ast.elem_type == InterpreterBase.NIL_NODE:
            return Interpreter.NIL_VALUE
        if expr_ast.elem_type == InterpreterBase.INT_NODE:
            return Value(Type.INT, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.STRING_NODE:
            return Value(Type.STRING, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.BOOL_NODE:
            return Value(Type.BOOL, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.VAR_NODE:
            var_name = expr_ast.get("name")
            if "." in var_name:
               return self.get_nested_field(var_name)
            else:
                val = self.env.get(var_name)
                if val is None:
                    super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
                return val
        if expr_ast.elem_type == InterpreterBase.FCALL_NODE:
            return self.__call_func(expr_ast)
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            return self.__eval_op(expr_ast)
        if expr_ast.elem_type == Interpreter.NEG_NODE:
            return self.__eval_unary(expr_ast, Type.INT, lambda x: -1 * x)
        if expr_ast.elem_type == Interpreter.NOT_NODE:
            return self.__eval_unary(expr_ast, Type.BOOL, lambda x: not x)

    def __eval_op(self, arith_ast):
        left_value_obj = self.__eval_expr(arith_ast.get("op1"))
        right_value_obj = self.__eval_expr(arith_ast.get("op2"))

        #if left_value_obj.type() == "BOOL" and right_value_obj.type() == "INT":
        unaccepted_types = ["int", "string", "bool", "void"]
        #print(left_value_obj.type())
        #print(right_value_obj.type())
        #print(left_value_obj.elem_type)
        #bool return set to int coercion
        if left_value_obj.type() == "bool" and right_value_obj.type() == "int":
            if right_value_obj.value() == 0:
                right_value_obj = Value(Type.BOOL, False)
            else:
                right_value_obj = Value(Type.BOOL, True)

        #bool return set to int coercion
        elif left_value_obj.type() == "int" and right_value_obj.type() == "bool":
            if left_value_obj.value() == 0:
                left_value_obj = Value(Type.BOOL, False)
            else:
                left_value_obj = Value(Type.BOOL, True)
        
        elif left_value_obj.type() == "int" and right_value_obj.type() == "int" and arith_ast.elem_type in ["||", "&&"]:
            if left_value_obj.value() == 0:
                left_value_obj = Value(Type.BOOL, False)
            else: 
                left_value_obj = Value(Type.BOOL, True)
            if right_value_obj.value() == 0:
                right_value_obj = Value(Type.BOOL, False)
            else:
                right_value_obj = Value(Type.BOOL, True)


        elif left_value_obj.type() in self.structs and right_value_obj.type() == "nil" and arith_ast.elem_type == "==":
            return Value(Type.BOOL, False)
        
        elif left_value_obj.type() in self.structs and right_value_obj.type() == "nil" and arith_ast.elem_type == "!=":
            return Value(Type.BOOL, True)
        
        elif (left_value_obj.type() in unaccepted_types) and right_value_obj.type() == "nil":
            super().error(
                ErrorType.TYPE_ERROR,
                f"Cannot compare {left_value_obj.type()} to nil",
            )

        elif (right_value_obj.type() in unaccepted_types) and left_value_obj.type() == "nil":
            super().error(
                ErrorType.TYPE_ERROR,
                f"Cannot compare {left_value_obj.type()} to nil",
            )

        if not self.__compatible_types(
            arith_ast.elem_type, left_value_obj, right_value_obj
        ):
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible types for {arith_ast.elem_type} operation",
            )
        if arith_ast.elem_type not in self.op_to_lambda[left_value_obj.type()]:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible operator {arith_ast.elem_type} for type {left_value_obj.type()}",
            )
        f = self.op_to_lambda[left_value_obj.type()][arith_ast.elem_type]
        return f(left_value_obj, right_value_obj)

    def __compatible_types(self, oper, obj1, obj2):
        # DOCUMENT: allow comparisons ==/!= of anything against anything
        if oper in ["==", "!="]:
            return True
        return obj1.type() == obj2.type()

    def __eval_unary(self, arith_ast, t, f):
        value_obj = self.__eval_expr(arith_ast.get("op1"))
        if value_obj.type() != t:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible type for {arith_ast.elem_type} operation",
            )
        return Value(t, f(value_obj.value()))

    def __setup_ops(self):
        self.op_to_lambda = {}
        # set up operations on integers
        self.op_to_lambda[Type.INT] = {}
        self.op_to_lambda[Type.INT]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.INT]["-"] = lambda x, y: Value(
            x.type(), x.value() - y.value()
        )
        self.op_to_lambda[Type.INT]["*"] = lambda x, y: Value(
            x.type(), x.value() * y.value()
        )
        self.op_to_lambda[Type.INT]["/"] = lambda x, y: Value(
            x.type(), x.value() // y.value()
        )
        self.op_to_lambda[Type.INT]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.INT]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )
        self.op_to_lambda[Type.INT]["<"] = lambda x, y: Value(
            Type.BOOL, x.value() < y.value()
        )
        self.op_to_lambda[Type.INT]["<="] = lambda x, y: Value(
            Type.BOOL, x.value() <= y.value()
        )
        self.op_to_lambda[Type.INT][">"] = lambda x, y: Value(
            Type.BOOL, x.value() > y.value()
        )
        self.op_to_lambda[Type.INT][">="] = lambda x, y: Value(
            Type.BOOL, x.value() >= y.value()
        )
        self.op_to_lambda[Type.INT]["&&"] = lambda x, y: Value(
            Type.BOOL, x.value() & y.value()
        )
        
        #  set up operations on strings
        self.op_to_lambda[Type.STRING] = {}
        self.op_to_lambda[Type.STRING]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.STRING]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.STRING]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )
        #  set up operations on bools
        self.op_to_lambda[Type.BOOL] = {}
        self.op_to_lambda[Type.BOOL]["&&"] = lambda x, y: Value(
            x.type(), x.value() and y.value()
        )
        self.op_to_lambda[Type.BOOL]["||"] = lambda x, y: Value(
            x.type(), x.value() or y.value()
        )
        self.op_to_lambda[Type.BOOL]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.BOOL]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

        #  set up operations on nil
        self.op_to_lambda[Type.NIL] = {}
        self.op_to_lambda[Type.NIL]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.NIL]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

    def __do_if(self, if_ast):
        cond_ast = if_ast.get("condition")
        result = self.__eval_expr(cond_ast)
        if result.type() == Type.INT:
            if result.value() == 0:
                result = Value(Type.BOOL, False) 
            else:
                result = Value(Type.BOOL, True)
        elif result.type() != Type.BOOL:
            super().error(
                ErrorType.TYPE_ERROR,
                "Incompatible type for if condition",
            )
        if result.value():
            statements = if_ast.get("statements")
            status, return_val = self.__run_statements(statements)
            return (status, return_val)
        else:
            else_statements = if_ast.get("else_statements")
            if else_statements is not None:
                status, return_val = self.__run_statements(else_statements)
                return (status, return_val)

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __do_for(self, for_ast):
        init_ast = for_ast.get("init") 
        cond_ast = for_ast.get("condition")
        update_ast = for_ast.get("update") 

        self.__run_statement(init_ast)  # initialize counter variable
        run_for = Interpreter.TRUE_VALUE
        while run_for.value():
            run_for = self.__eval_expr(cond_ast)  # check for-loop condition
            if run_for.type() == Type.INT:
                if run_for.value() == 0:
                    run_for = Value(Type.BOOL, False) 
                else:
                    run_for = Value(Type.BOOL, True)

            elif run_for.type() != Type.BOOL:
                super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible type for for condition",
                )

            if run_for.value():
                statements = for_ast.get("statements")
                status, return_val = self.__run_statements(statements)
                if status == ExecStatus.RETURN:
                    return status, return_val
                self.__run_statement(update_ast)  # update counter variable

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __do_return(self, return_ast):
    
        expr_ast = return_ast.get("expression")
        #print(expr_ast)

        if expr_ast is None:
            return (ExecStatus.RETURN, Interpreter.NIL_VALUE)
        
        elif expr_ast.elem_type == "var" and "." in expr_ast.get("name"):
            value_obj = self.__eval_expr(expr_ast)
            return (ExecStatus.RETURN, value_obj)
        
        
        elif expr_ast.elem_type == "var" and self.env.get(expr_ast.get("name")).type() in self.structs:
            value_obj = self.__eval_expr(expr_ast)
            #print("VAL OBJ")
            #print(value_obj)
            return (ExecStatus.RETURN, value_obj)
        
        else:
            value_obj = copy.copy(self.__eval_expr(expr_ast))
            #print("GOING THROUGH IT")
            return (ExecStatus.RETURN, value_obj)
        
        
    

interpreter = Interpreter()


program_source = """
func main() : int {
  var a: int; 
 
}

"""

interpreter.run(program_source)

