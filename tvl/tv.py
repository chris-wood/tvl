import sys
import json
import pycparser
from pycparser import c_generator

class FunctionTemplate(object):
    def __init__(self, jsonDescription):
        self.desc = jsonDescription
        self.name = jsonDescription["name"]
        self.count = 0

    def _produce_call(self, jsonVector):
        # need to produce the function invocation
        # and then the code ot run the check
        inputs = jsonVector["args"]
        outputs = jsonVector["outputs"]

        outputName = self.name + "_" + str(self.count)
        self.count += 1

        function = ""
        function = outputs[0]["type"] + " " + outputName + " = "
        function += self.name + "("

        count = 0
        for param in inputs:
            for slot in self.desc["params"]:
                if param["name"] == slot["name"]:
                    function += str(param["value"])
                    count += 1
                    if count < len(inputs):
                        function += ","
        function += ");"

        return outputName, function

    def _comparison_code(self, name, value, value_type):
        if value_type == "int":
            return name + " == " + str(value)
        elif value_type == "string":
            return "strcmp(" + name + ", " + str(value) + ") == 0"

    def _produce_check(self, name, jsonVector):
        # this will be language specific -- C will need to include asserts, for example, to make this run
        # comparison will also be language specific -- string comparison is == in python but strcmp(..) in C

        output = jsonVector["outputs"][0]

        check = "assert("
        check += self._comparison_code(name, str(output["value"]), output["type"])
        check += ");"

        return check


    def instantiate(self, jsonVector):
        name, function = self._produce_call(jsonVector)
        check = self._produce_check(name, jsonVector)

        return function, check


# pattern = FunctionTemplate(apiJson[0])
# function, check = pattern.instantiate(vectorJson[0])
# print function, check

class Program(object):
    def __init__(self, language, library):
        self.language = language
        self.library = library

    def generate_code(self, template, apiJSON, vectorJSON):
        pattern = FunctionTemplate(apiJson[0])
        function, check = pattern.instantiate(vectorJson[0])

        # code = template.header()
        code = """// INCLUDE YOUR HEADERS HERE
"""
        # code += generateHeaders()
        code += "#include \"" + self.library + "\"\n"
        code += "#include <assert.h>"
        code += """
int
main(int argc, char *argv[argc])
{
"""

        code += "    " + function + "\n"
        code += "    " + check + "\n"

        code += """    return 0;
}"""

        return code

class CHeader(object):
    def __init__(self, name, local):
        self.name = name
        self.local = local

    def compile(self):
        if self.local:
            return "#include \"" + self.name + "\""
        else:
            return "#include <" + self.name + ">"

class CExpression(object):
    def __init__(self, string):
        self.string = string

    def compile(self):
        return self.string

class CValue(object):
    def __init__(self, desc):
        self.desc = desc
        self.type = None
        self.name = None
        self.value = None
        self.__unpack()

    def __unpack(self):
        if "type" in self.desc:
            self.type = self.desc["type"]
        if "name" in self.desc:
            self.name = self.desc["name"]
        if "value" in self.desc:
            self.value = self.desc["value"]

    def type(self):
        return self.type

    def name(self):
        return self.name

    def value(self):
        return self.value

class CFunction(object):
    def __init__(self, description):
        self.desc = description
        self.body = []
        self.name = None
        self.parameters = []
        self.output = None
        self.__unpack()

    def __unpack(self):
        self.name = self.desc["name"]
        self.output = CValue(self.desc["outputs"][0])
        for param in self.desc["params"]:
            self.parameters.append(CValue(param))

    def add_expression(self, expression):
        self.body.append(expression)

    def signature(self):
        output = self.output.type
        output += " " + self.name + "("

        count = 0
        for param in self.parameters:
            output += param.type + " " + param.name
            count += 1
            if count < len(self.parameters):
                output += ","

        output += ")"

        return CExpression(output)

    def invocation(self, output_name, arguments):

        # 1. Generate the invocation
        code = self.output.type + " " + output_name + " = " + self.name
        code += "("

        count = 0
        for param in self.parameters:
            for arg in arguments:
                if arg.name == param.name:
                    code += str(arg.value)
                    count += 1
                    if count < len(self.parameters):
                        code += ","
        code += ")"

        return CExpression(code)


    def assertion(self, output_name, arguments):
        output_value = arguments[0]["value"]
        check = "assert("

        # check += self._comparison_code(output_name, str(output_value["value"]), output_value["type"])
        # check += output_variable.compare_to(output_value) -> produces a == 4

        check += ");"

        return CExpression(check)

    def compile(self):
        pass

class CProgram(Program):
    def __init__(self, library):
        self.headers = []
        self.headers.append(CHeader("assert.h", False))
        self.headers.append(CHeader(library, True))

        self.functions = []

    def add_header(self, header):
        self.headers.append(header)

    def add_function(self, function):
        self.functions.append(function)

    def compile(self):
        '''
        Assemble the code by walking the elements of the AST.
        This includes the following components:

        - Headers
        - Main function
            - Function calls and checks

        '''
        code = []
        for header in self.headers:
            code.append(header.compile())

        for functions in self.functions:
            code.extend(function.compile())

        return code

# program = Program("C", "add.h")
# code = program.generate_code(None, apiJson, vectorJson)

# XXX: main routine should be baked into the code
# mainFunction = CFunction({"name": "main", "outputs": [{ "type" : "int"}], "params": [{"name": "argc", "type": "int"}, {"name": "argv", "type":"char **"}] })
#
# arguments = []
# for arg in vectorJson[0]["args"]:
#     val = CValue(arg)
#     arguments.append(val)

# testFunction = CFunction(apiJson[0])
# invocation = testFunction.invocation("tmp", arguments)
# check = testFunction.assertion("tmp", vectorJson[0]["outputs"])
#
# print mainFunction.signature().compile()
# print invocation.compile()
# print check.compile()

#### TODO

# program = CProgram("add.h")
### XXX: create vectors from the JSON file, and for each one, add an invocation and check for each one to the main function

# program.add_function(mainFunction)

### latest

apiFile = sys.argv[1]
vectorFile = sys.argv[2]
templateFile = sys.argv[3]

with open(vectorFile, "r") as fh:
    text = fh.read()
    vectorJson = json.loads(text)

with open(templateFile, "r") as fh:
    template = fh.read()

with open(apiFile, "r") as fh:
    apiContents = fh.read()
apiParser = pycparser.c_parser.CParser()

apiAST = apiParser.parse(apiContents, filename='<none>')
apiAST.show()

print "*****"

# build a dictionary that maps function names to AST nodes
functions = {}
for node in apiAST.ext:
    if node.__class__.__name__ == "Decl":
        if node.type != None:
            if node.type.__class__.__name__ == "FuncDecl":
                function_decl = node.type
                name = function_decl.type.declname
                functions[name] = function_decl

# debug
print "Functions:", functions.keys()

for vector in vectorJson:
    function_name = vector["name"]
    if function_name not in functions:
        print >> sys.stderr, "Cannot generate vector for function %s" % function_name
        continue

    function_decl = functions[function_name]
    args = {}
    for arg in vector["args"]:
        name = arg["name"]
        arg_type = arg["type"]
        arg_value = arg["value"]
        args[name] = (arg_type, arg_value)

    # print args

    type_decl = pycparser.c_ast.TypeDecl("tmp", [], pycparser.c_ast.IdentifierType(["int"]))
    # type_decl.show()

    param_decl = []
    for arg in args:
        tup = args[arg]
        arg_type, arg_value = tup[0], tup[1]
        if arg_type == "int":
            value = pycparser.c_ast.Constant("int", str(arg_value))
            param_decl.append(value)
        else:
            raise Exception("Don't support other types yet")

    expr_list = pycparser.c_ast.ExprList(param_decl)
    # expr_list.show()

    call_decl = pycparser.c_ast.FuncCall(pycparser.c_ast.ID(function_name), expr_list)
    # call_decl.show()

    # XXX: learn more about what the parameters are
    assignment_decl = pycparser.c_ast.Decl(type_decl, [], [], [], type_decl, call_decl, [])
    block_decl = pycparser.c_ast.Compound([assignment_decl])

    

    ### build the AST that will generate the function call

    generator = c_generator.CGenerator()
    print generator.visit(block_decl)
