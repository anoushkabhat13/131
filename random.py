from brewparse import parse_program 

def main():
  # all programs will be provided to your interpreter as a python string, 
  # just as shown here.
    program_source = """func main() {
    var x;
    x = 5 + 6;
    print("The sum is: ", x);

"""
    parsed_program = parse_program(program_source)
    print(parsed_program)

 
 # this is how you use our parser to parse a valid Brewin program into 
