import typing
from typing import Any
from ast import *
import builtins
import inspect
import random
import ast

crypt_symbols = "".join([chr(x) for x in range(20388, 39715)])


def generate_random_name():
    return ''.join(random.choice(crypt_symbols) for _ in range(random.randint(5, 10)))


mappings = {}


def xor_string(text):
    return "".join([chr(ord(x) + 34070) for x in text])


xor_func_text = """
def xor(text):
    res = ""
    magic = 34070
    for i in text:
        if ord(i) > 20000:
            res += chr(ord(i) - magic)
        else:
            res += i
    return res
    
"""

def is_builtins(item):
    for i in vars(builtins):
        try:
            if item in vars(eval(f"builtins.{i}")):
                return True
        except Exception:
            pass

    for i in vars(typing):
        try:
            if item in vars(eval(f"typing.{i}")):
                return True
        except Exception:
            pass
    return False


def obf_element(node_name):
    is_crypto = False
    for s in str(node_name):
        if ord(s) > 20000:
            is_crypto = True
            break

    if node_name not in mappings and not is_crypto:
        mappings[node_name] = generate_random_name()

    return mappings[node_name] if node_name in mappings else node_name


def get_expression(number, type_num, mappings_):
    operands = ["+", "-", "/", "*", "%", "//"]
    expr_content = ""
    for i in range(random.randint(5, 7)):
        expr_content += str(random.randint(10, 100) + random.uniform(0.00000000001, 0.0000099999))
        expr_content += random.choice(operands)

    expr_content += str(random.randint(10, 20) + random.uniform(0.00000000001, 0.0000099999))
    magic_number = eval(expr_content) - number
    if type_num == "int":
        if "int" not in mappings_.keys():
            mappings_["int"] = generate_random_name()

        return f"{mappings_['int']}({expr_content}-{magic_number})"
    else:
        return f"{expr_content}-{magic_number}"


class CustomObfuscation(ast.NodeTransformer):
    def visit_Num(self, node):
        value = ast.parse(get_expression(node.value, "int", mappings))

        if isinstance(node.value, float):
            value = ast.parse(get_expression(node.value, "float", mappings))

        return value.body

    def visit_JoinedStr(self, node: JoinedStr) -> Any:
        for child in node.values[1:]:
            self.generic_visit(child)

        if isinstance(node.values[0], ast.Constant):
            if node.values[0].value == "":
                return node
            if "xor" not in mappings:
                mappings["xor"] = generate_random_name()
            func_call = ast.Call(func=ast.Name(id=mappings["xor"],
                                               ctx=ast.Load()),
                                 args=[node],
                                 keywords=[])

            node.values[0].value = xor_string(node.values[0].value)

            return ast.copy_location(func_call, node)
        return node

    def visit_Str(self, node: Str) -> Any:
        if node.value == "":
            return node
        if "xor" not in mappings:
            mappings["xor"] = generate_random_name()
        func_call = ast.Call(func=ast.Name(id=mappings["xor"],
                                           ctx=ast.Load()),
                             args=[node],
                             keywords=[])

        node.value = xor_string(node.value)

        return ast.copy_location(func_call, node)


def get_chars(text):
    result = ""
    for i in text:
        result += f"chr({ord(i)})+"
    return result[:-1]
def rename_code(main_code):
    # code = str(xor_func) + str(code)

    tree = ast.parse(main_code)
    mappings_text = ""
    last_import = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.count("__") == 2:
                continue
            node.name = obf_element(node.name)

        elif isinstance(node, ast.Name):
            if node.id.count("__") == 2:
                continue
            node.id = obf_element(node.id)

        elif isinstance(node, ast.Attribute):
            if node.attr.count("__") == 2:
                continue
            if is_builtins(node.attr):
                continue
            old_name = node.attr
            node.attr = obf_element(node.attr)

            if isinstance(node.value, ast.Name):
                old_module_name = node.value.id
                try:
                    module = inspect.getmodule(__import__(node.value.id))
                    if old_name in dir(module):
                        node.value.id = obf_element(node.value.id)
                        mappings_text += f"{mappings[old_name]} = {mappings[old_module_name]}.{old_name}\n"
                except ModuleNotFoundError:
                    pass

        elif isinstance(node, ast.ClassDef):
            node.name = obf_element(node.name)

        elif isinstance(node, ast.arguments):
            if node.args:
                for arg_ in node.args:
                    arg_.arg = obf_element(arg_.arg)

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    old_name = node.func.attr
                    if is_builtins(old_name):
                        continue
                    old_func_name = node.func.value.id
                    try:
                        inspect.getmodule(__import__(old_func_name))  # trying get module info

                        node.func.value.id = obf_element(node.func.value.id)
                        node.func.attr = obf_element(node.func.attr)
                        node.func = ast.Name(id=mappings[old_name], ctx=ast.Load())
                        mappings_text += f"{mappings[old_name]} = {mappings[old_func_name]}.{old_name}\n"
                    except ModuleNotFoundError:
                        pass

        ast.fix_missing_locations(node)

    obf_numbers = CustomObfuscation()
    obf_numbers.visit(tree)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            last_import = max(node.lineno, last_import)
            for name in node.names:
                if not name.asname and name.name in mappings:
                    name.asname = mappings[name.name]



        elif isinstance(node, ast.ImportFrom):
            last_import = max(node.lineno, last_import)
            for name in node.names:
                module = inspect.getmodule(__import__(node.module))
                if name.name == "*":
                    for m in mappings:
                        if m in dir(module):
                            mappings_text += f"{mappings[m]} = {m}\n"
                else:
                    if name.name not in mappings:
                        mappings_text += f"{name.name} = {name.name}\n"
                    else:
                        mappings_text += f"{mappings[name.name]} = {name.name}\n"

        ast.fix_missing_locations(node)

    for mapping in mappings.items():
        if hasattr(builtins, mapping[0]):
            mappings_text += f"{mapping[1]} = eval({get_chars(mapping[0])})\n"

    mappings_text = mappings_text.split("\n")
    mappings_text = set(mappings_text)
    mappings_text = "\n".join(mappings_text) + "\n"

    main_code = ast.unparse(tree)

    result_code = "# -*- coding: utf-8 -*-\n"
    for number_line, line in enumerate(main_code.split("\n")):
        if number_line == last_import:
            result_code += mappings_text + "\n"
            result_code += line + "\n"
        else:
            result_code += line + "\n"

    return result_code


foo = open("obfme.py", "r", encoding="utf-8").read()
foo = xor_func_text + "\n" + foo

new_code = rename_code(foo)

with open("result.py", "w", encoding="utf-8") as result:
    result.write(new_code.replace(" > \n        ", " > ").replace(" = \n    ", " = "))
