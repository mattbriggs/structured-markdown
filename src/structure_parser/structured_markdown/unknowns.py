"""Factory functions for unknown/fallback model objects."""
from structure_parser.contracts.structured_markdown import Attribute, Component, Unit
from structure_parser.domain.enums import AttributeType, ComponentType, TriageStatus, UnitType


def unknown_unit(content: list[Component], title: str | None = None) -> Unit:
    """Return a Unit of type unknown, wrapping the given components."""
    return Unit(
        unit_type=UnitType.unknown,
        title=title,
        triage_status=TriageStatus.unknown,
        content=content,
    )


def unknown_component(text: str | None = None) -> Component:
    """Return a Component of type compUnknown."""
    return Component(
        component_type=ComponentType.compUnknown,
        text=text,
        triage_status=TriageStatus.unknown,
    )


def unknown_attribute(text: str | None = None) -> Attribute:
    """Return an Attribute of type attUnknown."""
    return Attribute(
        att_type=AttributeType.attUnknown,
        text=text,
        triage_status=TriageStatus.unknown,
    )
