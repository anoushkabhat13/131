# The EnvironmentManager class keeps a mapping between each variable name (aka symbol)
# in a brewin program and the Value object, which stores a type, and a value.
from intbase import ErrorType
from type_valuev2 import Type, Value, create_value, get_printable



class EnvironmentManager:
    def __init__(self, interpreter_in):
        self.environment = []
        self.interpreter = interpreter_in

    # returns a VariableDef object
    def get(self, symbol):
        cur_func_env = self.environment[-1]
        for env in reversed(cur_func_env):
            if symbol in env:
                return env[symbol]

        return None

    def set(self, symbol, value):
        cur_func_env = self.environment[-1]
        for env in reversed(cur_func_env):
            if symbol in env:
                #coercing bool to int
                #print(symbol)
                #print(env[symbol].type())
                #print(value)
                #print(value.type())
                print("ENV SYMBOL TYPE")
                print(env[symbol].type())

                if (env[symbol].type() != 'int') and (env[symbol].type() != "bool") and (env[symbol].type()!= "String") and (value.type() == 'nil'):
                    env[symbol] = value

                if ((env[symbol].type() == "bool") and (value.type() == "int")):
                    if value.value() == 0:
                        env[symbol] = Value(Type.BOOL, False)
                    else:
                        env[symbol] = Value(Type.BOOL, True)

                
                elif (env[symbol].type() == "nil") and (value.type()!="int") and (value.type()!="bool") and (value.type()!="String"):
                    env[symbol] = value

                
                elif env[symbol].type() != value.type():
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        f"{symbol} has type {env[symbol].type()} but was set to a {value.type()}",
                    )

                env[symbol] = value
                return True

        return False

    # create a new symbol in the top-most environment, regardless of whether that symbol exists
    # in a lower environment
    def create(self, symbol, value):
        cur_func_env = self.environment[-1]
        if symbol in cur_func_env[-1]:   # symbol already defined in current scope
            return False
        cur_func_env[-1][symbol] = value
        return True

    # used when we enter a new function - start with empty dictionary to hold parameters.
    def push_func(self):
        self.environment.append([{}])  # [[...]] -> [[...], [{}]]

    def push_block(self):
        cur_func_env = self.environment[-1]
        cur_func_env.append({})  # [[...],[{....}] -> [[...],[{...}, {}]]

    def pop_block(self):
        cur_func_env = self.environment[-1]
        cur_func_env.pop() 

    # used when we exit a nested block to discard the environment for that block
    def pop_func(self):
        self.environment.pop()