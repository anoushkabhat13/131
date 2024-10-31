# The EnvironmentManager class keeps a mapping between each variable (aka symbol)
# in a brewin program and the value of that variable - the value that's passed in can be
# anything you like. In our implementation we pass in a Value object which holds a type
# and a value (e.g., Int, 10).
class EnvironmentManager:
    def __init__(self):
        self.environment = [{}] #make this into a list of environments

    # Gets the data associated a variable name
    def get(self, symbol):
        for current_scope in reversed(self.environment):
            if symbol in current_scope:
                return current_scope[symbol] 
            #if not go to next scope 
        return None
        

    # Sets the data associated with a variable name
    def set(self, symbol, value):
        for current_scope in reversed(self.environment):
            if symbol in current_scope:
                current_scope[symbol] = value
                return True
        return False

    def create(self, symbol, start_val):
        #if not in innermost scope (AKA current scope)
        if symbol not in self.environment[-1]: 
          self.environment[-1][symbol] = start_val 
          return True
        return False
    
    def add_scope(self):
        self.environment.append({})
    
    def remove_scope(self):
        if (len(self.environment) > 1):
            self.environment.pop()
        #else error
    