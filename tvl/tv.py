import sys
import json
import pycparser
from pycparser import c_generator

#  python tv.py ../apis/add.h ../vectors/add.json ../templates/c.txt

apiFile = sys.argv[1]
vectorFile = sys.argv[2]
# templateFile = sys.argv[3]

with open(vectorFile, "r") as fh:
    text = fh.read()
    vectorJson = json.loads(text)

# with open(templateFile, "r") as fh:
#     template = fh.read()

with open(apiFile, "r") as fh:
    apiContents = fh.read()
apiParser = pycparser.c_parser.CParser()

apiAST = apiParser.parse(apiContents, filename='<none>')
# apiAST.show()
# print "\n*****\n"

# build a dictionary that maps function names to AST nodes
functions = {}
for node in apiAST.ext:
    if node.__class__.__name__ == "Decl":
        if node.type != None:
            if node.type.__class__.__name__ == "FuncDecl":
                function_decl = node.type

                # XXX: we may need to do this more than once...
                # but the point here is to identify the name of the function, not its output type
                # XXX: as an additional check, we may store the output type and make sure it matches
                # those in the vectors
                if function_decl.type.__class__.__name__ == "PtrDecl":
                    function_decl = function_decl.type

                name = function_decl.type.declname
                functions[name] = function_decl

# For each test in the set of test vectors
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

    output = vector["output"]
    out_type = output["type"]
    out_value = output["value"]

    ### build the AST that will generate the function call

    type_decl = pycparser.c_ast.TypeDecl("tmp", [], pycparser.c_ast.IdentifierType([out_type]))

    param_decl = []
    for arg in args:
        tup = args[arg]
        arg_type, arg_value = tup[0], tup[1]
        if arg_type == "int":
            value = pycparser.c_ast.Constant("int", str(arg_value))
            param_decl.insert(0, value)
        elif arg_type == "char*":
            value = pycparser.c_ast.Constant("char *", str(arg_value))
            param_decl.insert(0, value)
        else:
            print arg_type
            raise Exception("Don't support other types yet")

    # Build the expression to be passed into the function call
    expr_list = pycparser.c_ast.ExprList(param_decl)

    # Build the actual invocation
    call_decl = pycparser.c_ast.FuncCall(pycparser.c_ast.ID(function_name), expr_list)

    # Build the assignment declaration
    assignment_decl = pycparser.c_ast.Decl(type_decl, [], [], [], type_decl, call_decl, [])

    # Build the AST that will generate the check code
    if out_type == "int":
        check_op = pycparser.c_ast.BinaryOp("==", pycparser.c_ast.ID(type_decl.declname), pycparser.c_ast.Constant(out_type, out_value))
    elif out_type == "char*":
        # Build string comparison block
        strcmp_expr_list = pycparser.c_ast.ExprList([pycparser.c_ast.ID(type_decl.declname), pycparser.c_ast.Constant(out_type, out_value)])
        strcmp_call_decl = pycparser.c_ast.FuncCall(pycparser.c_ast.ID("strcmp"), strcmp_expr_list)
        check_op = pycparser.c_ast.BinaryOp("==", strcmp_call_decl, pycparser.c_ast.Constant("int", 0))
    else: # we need to build the checks here
        raise Exception("Don't support non-int output types yet")

    # Build the check expression and function call declaration
    check_expr = pycparser.c_ast.ExprList([check_op])
    check_decl = pycparser.c_ast.FuncCall(pycparser.c_ast.ID("assert"), check_expr)

    # Build the BB from the first assignment and then from the corresponding check
    block_decl = pycparser.c_ast.Compound([assignment_decl, check_decl])

    # Generate the code
    generator = c_generator.CGenerator()

    print generator.visit(block_decl)

# op = pycparser.c_ast.BinaryOp("==", pycparser.c_ast.ID("tmp"), pycparser.c_ast.Constant("int", str(2)))
# op.show()
