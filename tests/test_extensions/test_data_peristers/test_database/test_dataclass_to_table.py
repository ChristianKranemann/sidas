# from dataclasses import Field, dataclass, fields
# from typing import Any, Tuple, get_args, get_origin

# from sqlalchemy import Integer


# @dataclass
# class AssetTest:
#     x: int = 1
#     y: int | None = None


# def type_tuple(f: Field) -> Tuple[Any, ...]:
#     f_type = f.type
#     if get_origin(f_type):
#         return get_args(f_type)
#     else:
#         return (f_type,)


# def is_optional(f: Field) -> bool:
#     return None in type_tuple(f)


# def test_get_field_type() -> None:
#     result = []
#     for f in fields(AssetTest):
#         if int in f_type_tuple:
#             result.append(Integer)

#     print(result)
