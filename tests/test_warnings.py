from mypy_upgrade.parsing import MypyError
from mypy_upgrade.warnings import create_not_silenced_errors_warning


class TestCreateNotSilencedErrorsWarning:
    @staticmethod
    def test_should_suggest_verbose_mode_if_column_numbers_specified_and_verbosity_is_less_than_one() -> (  # noqa: E501
        None
    ):
        warning = create_not_silenced_errors_warning(
            (MypyError("", 1, 0, "", ""),), verbosity=0
        )
        assert "(option -v)" in warning

    @staticmethod
    def test_should_not_suggest_verbose_mode_if_column_numbers_specified_and_verbosity_is_greater_than_one() -> (  # noqa: E501
        None
    ):
        warning = create_not_silenced_errors_warning(
            (MypyError("", 1, 0, "", ""),), verbosity=1
        )
        assert "(option -v)" not in warning
