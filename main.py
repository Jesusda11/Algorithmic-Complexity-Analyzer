from lexer.lexer import Lexer
from parser.parser import Parser

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    code = read_file("examples/sample1.txt")

    # 1. Lexer → convertir texto en tokens
    lexer = Lexer(code)
    tokens = lexer.tokenize()

    # 2. Parser → construir AST
    parser = Parser(tokens)
    ast = parser.parse()

    print(ast)
