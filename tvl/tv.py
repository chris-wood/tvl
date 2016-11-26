import sys
import json
import pycparser
from pycparser import c_generator

#  python tv.py ../apis/add.h ../vectors/add.json ../templates/c.txt

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
# print "Functions:", functions.keys()

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

    ### build the AST that will generate the function call

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

    # build the AST that will generate the check code
    # XXX: this should be sent to a function to do the comparison
    output_type = vector["outputs"][0]["type"]
    output_value = vector["outputs"][0]["value"]

    check_op = pycparser.c_ast.BinaryOp("==", pycparser.c_ast.ID(type_decl.declname), pycparser.c_ast.Constant(output_type, output_value))
    check_expr = pycparser.c_ast.ExprList([check_op])
    check_decl = pycparser.c_ast.FuncCall(pycparser.c_ast.ID("assert"), check_expr)

    block_decl = pycparser.c_ast.Compound([assignment_decl, check_decl])
    generator = c_generator.CGenerator()
    print generator.visit(block_decl)

# op = pycparser.c_ast.BinaryOp("==", pycparser.c_ast.ID("tmp"), pycparser.c_ast.Constant("int", str(2)))
# op.show()
