import sys
import json

# 1. read in the template
# 2. read in the API
# 3. read in the vectors and create the program

apiFile = sys.argv[1]
vectorFile = sys.argv[2]
templateFile = sys.argv[3]

with open(apiFile, "r") as fh:
    apiJson = json.loads(fh.read())

with open(vectorFile, "r") as fh:
    vectorJson = json.loads(fh.read())

with open(templateFile, "r") as fh:
    template = fh.read()

# print apiJson
# print vectorJson
# print template

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


pattern = FunctionTemplate(apiJson[0])
function, check = pattern.instantiate(vectorJson[0])
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

class CFunction(object):
    def __init__(self, description):
        self.desc = description
        self.body = []

    def add_expression(self, expression):
        self.body.append(expression)

    def signature(self):
        output = self.desc["output"]["type"]
        output += " " + self.desc["name"] + "("

        count = 0
        for param in self.desc["params"]:
            output += param["type"] + " " + param["name"]
            count += 1
            if count < len(self.desc["params"]):
                output += ","

        output += ")"

        return CExpression(output)

    def invocation(self, output, arguments):
        code = self.desc["outputs"][0]["type"] + " " + output + " = " + self.desc["name"]
        code += "("

        count = 0
        for param in self.desc["params"]:
            for arg in arguments:
                if arg["name"] == param["name"]:
                    code += str(arg["value"])
                    count += 1
                    if count < len(self.desc["params"]):
                        code += ","
        code += ")"

        return [CExpression(code)]

class CProgram(Program):
    def __init__(self, language, library):
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

program = Program("C", "add.h")
code = program.generate_code(None, apiJson, vectorJson)


# XXX: main routine should be standard function
mainFunction = CFunction({"name": "main", "output": { "type" : "int"}, "params": [{"name": "argc", "type": "int"}, {"name": "argv", "type":"char **"}] })
print mainFunction.signature().compile()

testFunction = CFunction(apiJson[0])
code = testFunction.invocation("tmp", vectorJson[0]["args"])
for c in map(lambda c : c.compile(), code):
    print c
