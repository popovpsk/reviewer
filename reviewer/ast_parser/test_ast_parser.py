# ruff: noqa
import pytest

from reviewer.ast_parser.ast_parser import ASTParser


@pytest.fixture
def ast_parser() -> ASTParser:
    return ASTParser()


class TestASTParser:
    def test_remove_python_function(self, ast_parser: ASTParser) -> None:
        content = """
def func_to_remove():
    pass

def func_to_keep():
    print("hello")
"""
        expected_content_after_removal = """

def func_to_keep():
    print("hello")
"""
        parsed_file = ast_parser.parse("1.py", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("func_to_remove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()
        # Test removing again (should fail)
        assert not parsed_file.remove_declaration("func_to_remove")

    def test_remove_python_class(self, ast_parser: ASTParser) -> None:
        content = """
class ClassToRemove:
    def method(self):
        pass

class ClassToKeep:
    pass
"""
        expected_content_after_removal = """

class ClassToKeep:
    pass
"""
        parsed_file = ast_parser.parse("test.py", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("ClassToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_python_decorated_function(self, ast_parser: ASTParser) -> None:
        content = """
@my_decorator
def decorated_func_to_remove():
    pass

def func_to_keep():
    pass
"""
        expected_content_after_removal = """

def func_to_keep():
    pass
"""
        parsed_file = ast_parser.parse("test.py", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("decorated_func_to_remove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_go_function(self, ast_parser: ASTParser) -> None:
        content = """
package main

func funcToRemove() {
    println("remove me")
}

func funcToKeep() {
    println("keep me")
}
"""
        expected_content_after_removal = """
package main



func funcToKeep() {
    println("keep me")
}
"""
        parsed_file = ast_parser.parse("test.go", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("funcToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_go_method(self, ast_parser: ASTParser) -> None:
        content = """
package main

type MyStruct struct{}

func (s *MyStruct) MethodToRemove() {
    println("remove me")
}

func (s *MyStruct) MethodToKeep() {
    println("keep me")
}
"""
        expected_content_after_removal = """
package main

type MyStruct struct{}



func (s *MyStruct) MethodToKeep() {
    println("keep me")
}
"""
        parsed_file = ast_parser.parse("test.go", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("MethodToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_go_type_spec(self, ast_parser: ASTParser) -> None:
        content = """
package main

type TypeToRemove struct {
    Field int
}

type TypeToKeep int
"""
        expected_content_after_removal = """
package main



type TypeToKeep int
"""
        parsed_file = ast_parser.parse("test.go", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("TypeToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_go_const_spec(self, ast_parser: ASTParser) -> None:
        content = """
package main

const (
    ConstToRemove = 1
    ConstToKeep = 2
)

const AnotherConst = 3
"""
        # Note: The current query removes only the specific const_spec,
        # not the whole const block if it's a parenthesized list.
        # This is generally fine. If ConstToKeep was on the same line, it would also be removed.
        # If the const block becomes empty, it might leave `const ()`.
        # For this test, we assume simple, separate const declarations or distinct lines in a block.
        expected_content_after_removal_specific = """
package main

const (
    
    ConstToKeep = 2
)

const AnotherConst = 3
"""
        parsed_file = ast_parser.parse("test.go", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("ConstToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal_specific.strip()

    def test_remove_non_existent_declaration(self, ast_parser: ASTParser) -> None:
        content = """
def existing_func():
    pass
"""
        parsed_file = ast_parser.parse("test.py", bytes(content, "utf-8"))
        assert parsed_file
        original_content_bytes = parsed_file.content
        assert not parsed_file.remove_declaration("non_existent_func")
        assert original_content_bytes == parsed_file.content

    def test_remove_python_variable_simple_assignment(self, ast_parser: ASTParser) -> None:
        content = """
var_to_remove = 42
var_to_keep = "hello"
"""
        expected_content_after_removal = """

var_to_keep = "hello"
"""
        parsed_file = ast_parser.parse("test.py", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("var_to_remove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_python_variable_typed_assignment(self, ast_parser: ASTParser) -> None:
        content = """
var_to_remove: int = 100
var_to_keep: str = "world"
"""
        expected_content_after_removal = """

var_to_keep: str = "world"
"""
        parsed_file = ast_parser.parse("test.py", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("var_to_remove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_python_variable_list_assignment(self, ast_parser: ASTParser) -> None:
        content = """
list_to_remove = [1, 2, 3]
list_to_keep = [4, 5, 6]
"""
        expected_content_after_removal = """

list_to_keep = [4, 5, 6]
"""
        parsed_file = ast_parser.parse("test.py", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("list_to_remove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_python_variable_dict_assignment(self, ast_parser: ASTParser) -> None:
        content = """
dict_to_remove = {"a": 1, "b": 2}
dict_to_keep = {"c": 3}
"""
        expected_content_after_removal = """

dict_to_keep = {"c": 3}
"""
        parsed_file = ast_parser.parse("test.py", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("dict_to_remove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_go_short_variable_declaration(self, ast_parser: ASTParser) -> None:
        content = """
package main

func main() {
    varToRemove := 123
    varToKeep := "hello"
    println(varToKeep)
}
"""
        expected_content_after_removal = """
package main

func main() {
    
    varToKeep := "hello"
    println(varToKeep)
}
"""
        parsed_file = ast_parser.parse("test.go", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("varToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_go_short_variable_map_declaration(self, ast_parser: ASTParser) -> None:
        content = """
package main

func main() {
    mapToRemove := map[string]int{"a": 1}
    mapToKeep := map[string]int{"b": 2}
    println(mapToKeep)
}
"""
        expected_content_after_removal = """
package main

func main() {
    
    mapToKeep := map[string]int{"b": 2}
    println(mapToKeep)
}
"""
        parsed_file = ast_parser.parse("test.go", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("mapToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_go_short_variable_slice_declaration(self, ast_parser: ASTParser) -> None:
        content = """
package main

func main() {
    sliceToRemove := []int{1, 2, 3}
    sliceToKeep := []string{"a", "b"}
    println(sliceToKeep)
}
"""
        expected_content_after_removal = """
package main

func main() {
    
    sliceToKeep := []string{"a", "b"}
    println(sliceToKeep)
}
"""
        parsed_file = ast_parser.parse("test.go", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("sliceToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_go_var_declaration_simple(self, ast_parser: ASTParser) -> None:
        content = """
package main

var varToRemove = 42
var varToKeep = "hello"
"""
        # Removing var_spec leaves the `var` keyword if it's the only spec.
        # This is consistent with const_spec removal.
        expected_content_after_removal = """
package main


var varToKeep = "hello"
"""
        parsed_file = ast_parser.parse("test.go", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("varToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_go_var_declaration_with_type(self, ast_parser: ASTParser) -> None:
        content = """
package main

var varToRemove int = 100
var varToKeep string = "world"
"""
        expected_content_after_removal = """
package main


var varToKeep string = "world"
"""
        parsed_file = ast_parser.parse("test.go", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("varToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_go_var_declaration_in_block(self, ast_parser: ASTParser) -> None:
        content = """
package main

var (
    VarToRemoveInBlock = "test"
    VarToKeepInBlock   = 123
)

var AnotherVar = true
"""
        expected_content_after_removal = """
package main

var (
    
    VarToKeepInBlock   = 123
)

var AnotherVar = true
"""
        parsed_file = ast_parser.parse("test.go", bytes(content, "utf-8"))
        assert parsed_file
        assert parsed_file.remove_declaration("VarToRemoveInBlock")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_go_var_declaration_multi_spec_line(self, ast_parser: ASTParser) -> None:
        # If multiple variables are declared in a single var_spec line,
        # and one is targeted, the entire var_spec line is removed.
        content = """
package main

var (
    Var1ToRemove, Var2ToRemove = "val1", "val2"
    Var3ToKeep = 10
)
"""
        expected_content_after_removal = """
package main

var (
    
    Var3ToKeep = 10
)
"""
        parsed_file = ast_parser.parse("test.go", bytes(content, "utf-8"))
        assert parsed_file is not None, "Parsing failed for Go content"
        # Targeting Var1ToRemove from "Var1ToRemove, Var2ToKeep" spec
        assert parsed_file.remove_declaration("Var1ToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_go_var_declaration_simple_in_function(self, ast_parser: ASTParser) -> None:
        content = """
package main

import "fmt"

func main() {
    var varToRemove = 42
    var varToKeep = "hello"
    fmt.Println(varToKeep)
}
"""
        expected_content_after_removal = """
package main

import "fmt"

func main() {
    
    var varToKeep = "hello"
    fmt.Println(varToKeep)
}
"""
        parsed_file = ast_parser.parse("test.go", bytes(content, "utf-8"))
        assert parsed_file is not None, "Parsing failed for Go content"
        assert parsed_file.remove_declaration("varToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()
        assert not parsed_file.remove_declaration("varToRemove")  # Test removing again

    def test_remove_go_var_declaration_with_type_in_function(self, ast_parser: ASTParser) -> None:
        content = """
package main

import "fmt"

func main() {
    type typeToRemove struct{}
    var varToKeep string = "world"
    fmt.Println(varToKeep)
}
"""
        expected_content_after_removal = """
package main

import "fmt"

func main() {
    
    var varToKeep string = "world"
    fmt.Println(varToKeep)
}
"""
        parsed_file = ast_parser.parse("test.go", bytes(content, "utf-8"))
        assert parsed_file is not None, "Parsing failed for Go content"
        assert parsed_file.remove_declaration("typeToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()
        assert not parsed_file.remove_declaration("varToRemove")  # Test removing again

    def test_remove_proto_message(self, ast_parser: ASTParser) -> None:
        content = """
syntax = "proto3";

message MessageToRemove {
  string field1 = 1;
}

message MessageToKeep {
  int32 field2 = 1;
}
"""
        expected_content_after_removal = """
syntax = "proto3";



message MessageToKeep {
  int32 field2 = 1;
}
"""
        parsed_file = ast_parser.parse("test.proto", bytes(content, "utf-8"))
        assert parsed_file, "Parsing .proto file failed"
        assert parsed_file.remove_declaration("MessageToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()
        assert not parsed_file.remove_declaration("MessageToRemove")

    def test_remove_proto_rpc(self, ast_parser: ASTParser) -> None:
        content = """
syntax = "proto3";

service MyService {
  rpc RpcToRemove (RequestType) returns (ResponseType);
  rpc RpcToKeep (AnotherRequest) returns (AnotherResponse);
}

message RequestType {}
message ResponseType {}
message AnotherRequest {}
message AnotherResponse {}
"""
        expected_content_after_removal = """
syntax = "proto3";

service MyService {
  
  rpc RpcToKeep (AnotherRequest) returns (AnotherResponse);
}

message RequestType {}
message ResponseType {}
message AnotherRequest {}
message AnotherResponse {}
"""
        parsed_file = ast_parser.parse("test.proto", bytes(content, "utf-8"))
        assert parsed_file, "Parsing .proto file failed"
        assert parsed_file.remove_declaration("RpcToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()
        assert not parsed_file.remove_declaration("RpcToRemove")

    def test_remove_typescript_function(self, ast_parser: ASTParser) -> None:
        content = """
function funcToRemove(): void {
    console.log("remove me");
}

function funcToKeep(): string {
    return "keep me";
}
"""
        expected_content_after_removal = """

function funcToKeep(): string {
    return "keep me";
}
"""
        parsed_file = ast_parser.parse("test.ts", bytes(content, "utf-8"))
        assert parsed_file, "Parsing TypeScript file failed"
        assert parsed_file.remove_declaration("funcToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()
        assert not parsed_file.remove_declaration("funcToRemove")

    def test_remove_typescript_class(self, ast_parser: ASTParser) -> None:
        content = """
class ClassToRemove {
    method() {
        console.log("remove me");
    }
}

class ClassToKeep {
    method() {
        console.log("keep me");
    }
}
"""
        expected_content_after_removal = """

class ClassToKeep {
    method() {
        console.log("keep me");
    }
}
"""
        parsed_file = ast_parser.parse("test.ts", bytes(content, "utf-8"))
        assert parsed_file, "Parsing TypeScript file failed"
        assert parsed_file.remove_declaration("ClassToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_typescript_interface(self, ast_parser: ASTParser) -> None:
        content = """
interface InterfaceToRemove {
    prop: string;
}

interface InterfaceToKeep {
    prop: number;
}
"""
        expected_content_after_removal = """

interface InterfaceToKeep {
    prop: number;
}
"""
        parsed_file = ast_parser.parse("test.ts", bytes(content, "utf-8"))
        assert parsed_file, "Parsing TypeScript file failed"
        assert parsed_file.remove_declaration("InterfaceToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_typescript_type_alias(self, ast_parser: ASTParser) -> None:
        content = """
type TypeToRemove = string;
type TypeToKeep = number;
"""
        expected_content_after_removal = """

type TypeToKeep = number;
"""
        parsed_file = ast_parser.parse("test.ts", bytes(content, "utf-8"))
        assert parsed_file, "Parsing TypeScript file failed"
        assert parsed_file.remove_declaration("TypeToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()

    def test_remove_typescript_enum(self, ast_parser: ASTParser) -> None:
        content = """
enum EnumToRemove {
    Value1,
    Value2
}

enum EnumToKeep {
    ValueA,
    ValueB
}
"""
        expected_content_after_removal = """

enum EnumToKeep {
    ValueA,
    ValueB
}
"""
        parsed_file = ast_parser.parse("test.ts", bytes(content, "utf-8"))
        assert parsed_file, "Parsing TypeScript file failed"
        assert parsed_file.remove_declaration("EnumToRemove")
        assert parsed_file.content.decode("utf-8").strip() == expected_content_after_removal.strip()
