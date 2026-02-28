"""Tests for the FrozenMeta metaclass (immutability of Color and Style)."""

import pytest

from pyansistring.constants import SGR
from pyansistring.style import Color, Style


@pytest.fixture(
    params=[
        pytest.param(lambda: Color.from_8bit(100), id="Color"),
        pytest.param(lambda: Style(attributes=frozenset({SGR.BOLD})), id="Style"),
    ]
)
def frozen_instance(request: pytest.FixtureRequest):
    """Yield a frozen Color or Style instance."""
    return request.param()


class TestFrozenMeta:
    """Instances created with FrozenMeta should reject attribute mutation."""

    def test_cannot_set_existing_attribute(self, frozen_instance: object):
        """Existing attributes must not be overwritable."""
        attr = next(iter(vars(frozen_instance)))  # pick the first real attr
        with pytest.raises(AttributeError, match="read-only"):
            setattr(frozen_instance, attr, "new_value")

    def test_cannot_set_new_attribute(self, frozen_instance: object):
        """Adding a brand-new attribute must be rejected."""
        with pytest.raises(AttributeError, match="has not attribute"):
            setattr(frozen_instance, "totally_new_attr", 42)

    def test_cannot_delete_attribute(self, frozen_instance: object):
        """Deleting an existing attribute must be rejected."""
        attr = next(iter(vars(frozen_instance)))
        with pytest.raises(AttributeError, match="read-only"):
            delattr(frozen_instance, attr)
