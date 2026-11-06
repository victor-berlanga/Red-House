"""Declared laboratory data, never an inference of transplantability."""

import re
from typing import Annotated, Literal

from pydantic import Field, model_validator
from redhouse.models import Model, Text

# Both identifiers name the same 2010 colon nomenclature. The second identifies
# this corrected technical validator, not a laboratory allele-database release.
SUPPORTED_SYNTAX = {
    "2010": r"\*\d{2,}(?::\d{2,}){1,3}[NLSCAQ]?$",
    "2010:syntax-2": r"\*\d{2,}(?::\d{2,}){1,3}[NLSCAQ]?$",
}


class Locus(Model):
    locus: Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9]{0,15}$")]
    alleles: Annotated[list[Text], Field(max_length=16)]
    ambiguous: bool = False
    groups: Annotated[list[Text], Field(max_length=16)] = Field(default_factory=list)
    partial: bool = False

    @model_validator(mode="after")
    def syntax(self):
        # Syntax only, not membership in a particular IPD-IMGT/HLA release.
        if not self.alleles and not self.groups:
            raise ValueError("Tipificación requiere alelos o grupos declarados")
        if self.groups and (
            not self.partial
            or any(
                not re.fullmatch(re.escape(self.locus) + r"\*\d{2,}", x)
                for x in self.groups
            )
        ):
            raise ValueError(
                "Grupo de un campo requiere tipificación parcial explícita"
            )
        if len(set(self.alleles)) != len(self.alleles):
            raise ValueError("Alternativas duplicadas")
        return self


class Typing(Model):
    nomenclature: Literal["HLA-colon-2010"]
    nomenclature_version: Literal["2010", "2010:syntax-2"]
    resolution: Text
    catalogue_version: Text | None = None
    loci: Annotated[list[Locus], Field(min_length=1, max_length=80)]

    @model_validator(mode="after")
    def unique(self):
        syntax = SUPPORTED_SYNTAX[self.nomenclature_version]
        for locus in self.loci:
            if any(
                not re.fullmatch(re.escape(locus.locus) + syntax, a)
                for a in locus.alleles
            ):
                raise ValueError(
                    "Alelo fuera de la sintaxis HLA seleccionada; los grupos parciales se registran por separado"
                )
        if len({x.locus for x in self.loci}) != len(self.loci):
            raise ValueError("Loci duplicados")
        return self
