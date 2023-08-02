import pytest

from mypy_upgrade.filter import filter_mypy_errors
from mypy_upgrade.parsing import MypyError


@pytest.fixture(
    name="packages_to_include",
    params=(
        [],
        ["ase"],
        ["ase.calculators"],
        ["collections"],
        ["ase.geometry", "ase.dft"],
    ),
)
def fixture_packages_to_include(request: pytest.FixtureRequest) -> list[str]:
    return request.param


@pytest.fixture(
    name="modules_to_include",
    params=(
        [],
        ["ase.atoms"],
        ["ase.dft.wannierstate"],
        ["collections"],
        ["ase.atom", "ase.ga.population"],
    ),
)
def fixture_modules_to_include(request: pytest.FixtureRequest) -> list[str]:
    return request.param


@pytest.fixture(
    name="files_to_include",
    params=(
        [],
        ["ase/ga/population.py"],
        ["ase/neighborlist.py"],
        ["ase/__init__.py"],
        ["ase/io/bundletrajectory.py", "aase/thermochemistry.py"],
    ),
)
def fixture_files_to_include(request: pytest.FixtureRequest) -> list[str]:
    return request.param


@pytest.mark.slow
def test_should_only_include_selected_packages(
    parsed_errors: list[MypyError], packages_to_include: list[str]
) -> None:
    filtered_errors = filter_mypy_errors(
        parsed_errors, packages_to_include, [], []
    )
    if packages_to_include:
        packages_supposed_to_be_included = []
        for error in filtered_errors:
            packages_supposed_to_be_included.append(
                any(p in error.filename for p in packages_to_include)
            )
        assert all(packages_supposed_to_be_included)
    else:
        assert filtered_errors == parsed_errors


@pytest.mark.slow
def test_should_only_include_selected_modules(
    parsed_errors: list[MypyError], modules_to_include: list[str]
) -> None:
    filtered_errors = filter_mypy_errors(
        parsed_errors, modules_to_include, [], []
    )
    if modules_to_include:
        modules_supposed_to_be_included = []
        for error in filtered_errors:
            modules_supposed_to_be_included.append(
                any(m in error.filename for m in modules_to_include)
            )
        assert all(modules_supposed_to_be_included)
    else:
        assert filtered_errors == parsed_errors


@pytest.mark.slow
def test_should_only_include_selected_files(
    parsed_errors: list[MypyError], files_to_include: list[str]
) -> None:
    filtered_errors = filter_mypy_errors(
        parsed_errors, [], [], files_to_include
    )
    if files_to_include:
        assert all(
            error.filename in files_to_include for error in filtered_errors
        )
    else:
        assert filtered_errors == parsed_errors


@pytest.mark.slow
def test_should_only_include_selected_combinations(
    parsed_errors: list[MypyError],
    packages_to_include: list[str],
    modules_to_include: list[str],
    files_to_include: list[str],
) -> None:
    filtered_errors = filter_mypy_errors(
        parsed_errors,
        packages_to_include,
        modules_to_include,
        files_to_include,
    )

    to_include = packages_to_include + modules_to_include + files_to_include
    if to_include:
        supposed_to_be_included = []
        for error in filtered_errors:
            supposed_to_be_included.append(
                any(path in error.filename for path in to_include)
            )
        assert all(supposed_to_be_included)
    else:
        assert filtered_errors == parsed_errors
