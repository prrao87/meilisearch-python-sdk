import pytest
from httpx import Response

from meilisearch_python_sdk._http_requests import AsyncHttpRequests
from meilisearch_python_sdk._task import async_wait_for_task
from meilisearch_python_sdk.errors import MeilisearchApiError
from meilisearch_python_sdk.models.settings import (
    Faceting,
    MeilisearchSettings,
    MinWordSizeForTypos,
    Pagination,
    TypoTolerance,
)


@pytest.fixture
def new_settings():
    return MeilisearchSettings(
        ranking_rules=["typo", "words"],
        searchable_attributes=["title", "overview"],
        sortable_attributes=["genre", "title"],
        typo_tolerance=TypoTolerance(enabled=False),
        faceting=Faceting(max_values_per_facet=123),
        pagination=Pagination(max_total_hits=17),
        separator_tokens=["&sep", "/", "|"],
        non_separator_tokens=["#", "@"],
        dictionary=["S.O", "S.O.S"],
    )


@pytest.fixture
def default_ranking_rules():
    return ["words", "typo", "proximity", "attribute", "sort", "exactness"]


@pytest.fixture
def default_faceting():
    return Faceting(max_values_per_facet=100, sort_facet_values_by={"*": "alpha"})


@pytest.fixture
def new_ranking_rules():
    return ["typo", "exactness"]


@pytest.fixture
def new_distinct_attribute():
    return "title"


@pytest.fixture
def default_distinct_attribute():
    return None


@pytest.fixture
def new_searchable_attributes():
    return ["something", "random"]


@pytest.fixture
def displayed_attributes():
    return ["id", "release_date", "title", "poster", "overview", "genre"]


@pytest.fixture
def new_stop_words():
    return ["of", "the"]


@pytest.fixture
def new_synonyms():
    return {"hp": ["harry potter"]}


@pytest.fixture
def filterable_attributes():
    return ["release_date", "title"]


@pytest.fixture
def default_pagination():
    return Pagination(max_total_hits=1000)


@pytest.fixture
def sortable_attributes():
    return ["genre", "title"]


@pytest.mark.usefixtures("indexes_sample")
async def test_delete_index(async_test_client, index_uid, index_uid2):
    response = await async_test_client.index(uid=index_uid).delete()
    await async_wait_for_task(async_test_client, response.task_uid)

    with pytest.raises(MeilisearchApiError):
        await async_test_client.get_index(uid=index_uid)

    response = await async_test_client.index(uid=index_uid2).delete()
    await async_wait_for_task(async_test_client, response.task_uid)

    with pytest.raises(MeilisearchApiError):
        await async_test_client.get_index(uid=index_uid2)

    indexes = await async_test_client.get_indexes()
    assert indexes is None


@pytest.mark.usefixtures("indexes_sample")
async def test_update_index(async_test_client, index_uid):
    index = async_test_client.index(uid=index_uid)
    await index.update(primary_key="objectID")

    assert index.primary_key == "objectID"
    assert await index.get_primary_key() == "objectID"


async def test_get_stats(async_empty_index, small_movies):
    index = await async_empty_index()
    update = await index.add_documents(small_movies)
    await async_wait_for_task(index.http_client, update.task_uid)
    response = await index.get_stats()

    assert response.number_of_documents == 30


async def test_get_settings_default(
    async_empty_index, default_ranking_rules, default_faceting, default_pagination
):
    index = await async_empty_index()
    response = await index.get_settings()
    assert response.ranking_rules == default_ranking_rules
    assert response.distinct_attribute is None
    assert response.searchable_attributes == ["*"]
    assert response.displayed_attributes == ["*"]
    assert response.stop_words == []
    assert response.synonyms == {}
    assert response.sortable_attributes == []
    assert response.typo_tolerance.enabled is True
    assert response.faceting == default_faceting
    assert response.pagination == default_pagination
    assert response.separator_tokens == []
    assert response.non_separator_tokens == []
    assert response.dictionary == []


async def test_update_settings(async_empty_index, new_settings):
    index = await async_empty_index()
    response = await index.update_settings(new_settings)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_settings()
    assert response.ranking_rules == new_settings.ranking_rules
    assert response.distinct_attribute is None
    assert response.searchable_attributes == new_settings.searchable_attributes
    assert response.displayed_attributes == ["*"]
    assert response.stop_words == []
    assert response.synonyms == {}
    assert response.sortable_attributes == new_settings.sortable_attributes
    assert response.typo_tolerance.enabled is False
    assert (
        response.faceting.max_values_per_facet == new_settings.faceting.max_values_per_facet == 123
    )
    assert response.pagination == new_settings.pagination
    assert response.separator_tokens == new_settings.separator_tokens
    assert response.non_separator_tokens == new_settings.non_separator_tokens
    assert response.dictionary == new_settings.dictionary


async def test_reset_settings(async_empty_index, new_settings, default_ranking_rules):
    index = await async_empty_index()
    response = await index.update_settings(new_settings)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_settings()
    assert response.ranking_rules == new_settings.ranking_rules
    assert response.distinct_attribute is None
    assert response.searchable_attributes == new_settings.searchable_attributes
    assert response.displayed_attributes == ["*"]
    assert response.stop_words == []
    assert response.synonyms == {}
    assert response.sortable_attributes == new_settings.sortable_attributes
    assert response.typo_tolerance.enabled is False
    assert response.pagination == new_settings.pagination
    response = await index.reset_settings()
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_settings()
    assert response.ranking_rules == default_ranking_rules
    assert response.distinct_attribute is None
    assert response.displayed_attributes == ["*"]
    assert response.searchable_attributes == ["*"]
    assert response.stop_words == []
    assert response.synonyms == {}
    assert response.sortable_attributes == []
    assert response.typo_tolerance.enabled is True
    assert response.faceting.max_values_per_facet == 100
    assert response.pagination.max_total_hits == 1000


async def test_get_ranking_rules_default(async_empty_index, default_ranking_rules):
    index = await async_empty_index()
    response = await index.get_ranking_rules()
    assert response == default_ranking_rules


async def test_update_ranking_rules(async_empty_index, new_ranking_rules):
    index = await async_empty_index()
    response = await index.update_ranking_rules(new_ranking_rules)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_ranking_rules()
    assert response == new_ranking_rules


@pytest.mark.asyncio
async def test_reset_ranking_rules(async_empty_index, new_ranking_rules, default_ranking_rules):
    index = await async_empty_index()
    response = await index.update_ranking_rules(new_ranking_rules)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_ranking_rules()
    assert response == new_ranking_rules
    response = await index.reset_ranking_rules()
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_ranking_rules()
    assert response == default_ranking_rules


async def test_get_distinct_attribute(async_empty_index, default_distinct_attribute):
    index = await async_empty_index()
    response = await index.get_distinct_attribute()
    assert response == default_distinct_attribute


async def test_update_distinct_attribute(async_empty_index, new_distinct_attribute):
    index = await async_empty_index()
    response = await index.update_distinct_attribute(new_distinct_attribute)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_distinct_attribute()
    assert response == new_distinct_attribute


async def test_reset_distinct_attribute(
    async_empty_index, new_distinct_attribute, default_distinct_attribute
):
    index = await async_empty_index()
    response = await index.update_distinct_attribute(new_distinct_attribute)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_distinct_attribute()
    assert response == new_distinct_attribute
    response = await index.reset_distinct_attribute()
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_distinct_attribute()
    assert response == default_distinct_attribute


async def test_get_searchable_attributes(async_empty_index, small_movies):
    index = await async_empty_index()
    response = await index.get_searchable_attributes()
    assert response == ["*"]
    response = await index.add_documents(small_movies, primary_key="id")
    await async_wait_for_task(index.http_client, response.task_uid)
    get_attributes = await index.get_searchable_attributes()
    assert get_attributes == ["*"]


async def test_update_searchable_attributes(async_empty_index, new_searchable_attributes):
    index = await async_empty_index()
    response = await index.update_searchable_attributes(new_searchable_attributes)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_searchable_attributes()
    assert response == new_searchable_attributes


async def test_reset_searchable_attributes(async_empty_index, new_searchable_attributes):
    index = await async_empty_index()
    response = await index.update_searchable_attributes(new_searchable_attributes)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_searchable_attributes()
    assert response == new_searchable_attributes
    response = await index.reset_searchable_attributes()
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_searchable_attributes()
    assert response == ["*"]


async def test_get_displayed_attributes(async_empty_index, small_movies):
    index = await async_empty_index()
    response = await index.get_displayed_attributes()
    assert response == ["*"]
    response = await index.add_documents(small_movies)
    await async_wait_for_task(index.http_client, response.task_uid)
    get_attributes = await index.get_displayed_attributes()
    assert get_attributes == ["*"]


async def test_update_displayed_attributes(async_empty_index, displayed_attributes):
    index = await async_empty_index()
    response = await index.update_displayed_attributes(displayed_attributes)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_displayed_attributes()
    assert response == displayed_attributes


async def test_reset_displayed_attributes(async_empty_index, displayed_attributes):
    index = await async_empty_index()
    response = await index.update_displayed_attributes(displayed_attributes)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_displayed_attributes()
    assert response == displayed_attributes
    response = await index.reset_displayed_attributes()
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_displayed_attributes()
    assert response == ["*"]


async def test_get_pagination(async_empty_index):
    index = await async_empty_index()
    response = await index.get_pagination()
    assert response.max_total_hits == 1000


async def test_update_pagination(async_empty_index):
    pagination = Pagination(max_total_hits=17)
    index = await async_empty_index()
    response = await index.update_pagination(pagination)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_pagination()
    assert pagination.model_dump() == pagination.model_dump()


async def test_reset_pagination(async_empty_index, default_pagination):
    index = await async_empty_index()
    response = await index.update_pagination(Pagination(max_total_hits=17))
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.reset_pagination()
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_pagination()
    assert response.model_dump() == default_pagination.model_dump()


async def test_get_separator_tokens(async_empty_index):
    index = await async_empty_index()
    response = await index.get_separator_tokens()
    assert response == []


async def test_update_separator_tokens(async_empty_index):
    index = await async_empty_index()
    expected = ["/", "|"]
    response = await index.update_separator_tokens(expected)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_separator_tokens()
    assert response == expected


async def test_reset_separator_tokens(async_empty_index):
    index = await async_empty_index()
    expected = ["/", "|"]
    response = await index.update_separator_tokens(expected)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_separator_tokens()
    assert response == expected
    response = await index.reset_separator_tokens()
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_separator_tokens()
    assert response == []


async def test_get_non_separator_tokens(async_empty_index):
    index = await async_empty_index()
    response = await index.get_non_separator_tokens()
    assert response == []


async def test_update_non_separator_tokens(async_empty_index):
    index = await async_empty_index()
    expected = ["#", "@"]
    response = await index.update_non_separator_tokens(expected)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_non_separator_tokens()
    assert response == expected


async def test_reset_non_separator_tokens(async_empty_index):
    index = await async_empty_index()
    expected = ["#", "@"]
    response = await index.update_non_separator_tokens(expected)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_non_separator_tokens()
    assert response == expected
    response = await index.reset_non_separator_tokens()
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_non_separator_tokens()
    assert response == []


async def test_get_word_dictionary(async_empty_index):
    index = await async_empty_index()
    response = await index.get_word_dictionary()
    assert response == []


async def test_update_word_dictionary(async_empty_index):
    index = await async_empty_index()
    expected = ["S.O", "S.O.S"]
    response = await index.update_word_dictionary(expected)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_word_dictionary()
    assert response == expected


async def test_reset_word_dictionary(async_empty_index):
    index = await async_empty_index()
    expected = ["S.O", "S.O.S"]
    response = await index.update_word_dictionary(expected)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_word_dictionary()
    assert response == expected
    response = await index.reset_word_dictionary()
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_word_dictionary()
    assert response == []


async def test_get_stop_words_default(async_empty_index):
    index = await async_empty_index()
    response = await index.get_stop_words()
    assert response is None


async def test_update_stop_words(async_empty_index, new_stop_words):
    index = await async_empty_index()
    response = await index.update_stop_words(new_stop_words)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_stop_words()
    assert response == new_stop_words


async def test_reset_stop_words(async_empty_index, new_stop_words):
    index = await async_empty_index()
    response = await index.update_stop_words(new_stop_words)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_stop_words()
    assert response == new_stop_words
    response = await index.reset_stop_words()
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_stop_words()
    assert response is None


async def test_get_synonyms_default(async_empty_index):
    index = await async_empty_index()
    response = await index.get_synonyms()
    assert response is None


async def test_update_synonyms(async_empty_index, new_synonyms):
    index = await async_empty_index()
    response = await index.update_synonyms(new_synonyms)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_synonyms()
    assert response == new_synonyms


async def test_reset_synonyms(async_empty_index, new_synonyms):
    index = await async_empty_index()
    response = await index.update_synonyms(new_synonyms)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_synonyms()
    assert response == new_synonyms
    response = await index.reset_synonyms()
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_synonyms()
    assert response is None


async def test_get_filterable_attributes(async_empty_index):
    index = await async_empty_index()
    response = await index.get_filterable_attributes()
    assert response is None


async def test_update_filterable_attributes(async_empty_index, filterable_attributes):
    index = await async_empty_index()
    response = await index.update_filterable_attributes(filterable_attributes)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_filterable_attributes()
    assert sorted(response) == filterable_attributes


async def test_reset_filterable_attributes(async_empty_index, filterable_attributes):
    index = await async_empty_index()
    response = await index.update_filterable_attributes(filterable_attributes)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_filterable_attributes()
    assert sorted(response) == filterable_attributes
    response = await index.reset_filterable_attributes()
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_filterable_attributes()
    assert response is None


async def test_get_sortable_attributes(async_empty_index):
    index = await async_empty_index()
    response = await index.get_sortable_attributes()
    assert response == []


async def test_update_sortable_attributes(async_empty_index, sortable_attributes):
    index = await async_empty_index()
    response = await index.update_sortable_attributes(sortable_attributes)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_sortable_attributes()
    assert sorted(response) == sortable_attributes


async def test_reset_sortable_attributes(async_empty_index, sortable_attributes):
    index = await async_empty_index()
    response = await index.update_sortable_attributes(sortable_attributes)
    update = await async_wait_for_task(index.http_client, response.task_uid)
    assert update.status == "succeeded"
    response = await index.get_sortable_attributes()
    assert response == sortable_attributes
    response = await index.reset_sortable_attributes()
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_sortable_attributes()
    assert response == []


async def test_get_typo_tolerance(async_empty_index):
    index = await async_empty_index()
    response = await index.get_typo_tolerance()
    assert response.enabled is True


async def test_update_typo_tolerance(async_empty_index):
    typo_tolerance = TypoTolerance(
        enabled=True,
        disable_on_attributes=["title"],
        disable_on_words=["spiderman"],
        min_word_size_for_typos=MinWordSizeForTypos(one_typo=10, two_typos=20),
    )
    index = await async_empty_index()
    response = await index.update_typo_tolerance(typo_tolerance)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_typo_tolerance()
    assert response.model_dump() == typo_tolerance.model_dump()


async def test_reset_typo_tolerance(async_empty_index):
    index = await async_empty_index()
    response = await index.update_typo_tolerance(TypoTolerance(enabled=False))
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.reset_typo_tolerance()
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_typo_tolerance()
    assert response.enabled is True


async def test_get_faceting(async_empty_index):
    index = await async_empty_index()
    response = await index.get_faceting()
    assert response.max_values_per_facet == 100


async def test_update_faceting(async_empty_index):
    faceting = Faceting(max_values_per_facet=17)
    index = await async_empty_index()
    response = await index.update_faceting(faceting)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_faceting()
    expected = faceting.model_dump()
    expected["sort_facet_values_by"] = {"*": "alpha"}
    assert response.model_dump() == expected


@pytest.mark.parametrize(
    "index_name, facet_order, max_values_per_facet, expected",
    [
        ("*", "alpha", 17, {"max_values_per_facet": 17, "sort_facet_values_by": {"*": "alpha"}}),
        ("*", "count", 41, {"max_values_per_facet": 41, "sort_facet_values_by": {"*": "count"}}),
        (
            "movies",
            "alpha",
            42,
            {"max_values_per_facet": 42, "sort_facet_values_by": {"*": "alpha", "movies": "alpha"}},
        ),
        (
            "movies",
            "alpha",
            73,
            {"max_values_per_facet": 73, "sort_facet_values_by": {"*": "alpha", "movies": "alpha"}},
        ),
    ],
)
async def test_update_faceting_sort_facet_values(
    index_name, facet_order, max_values_per_facet, expected, async_empty_index
):
    faceting = Faceting(
        max_values_per_facet=max_values_per_facet,
        sort_facet_values_by={index_name: facet_order},
    )
    index = await async_empty_index()
    response = await index.update_faceting(faceting)
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_faceting()
    assert response.model_dump() == expected


def test_update_faceting_sort_facet_values_invalid_sort_type():
    with pytest.raises(ValueError):
        Faceting(
            max_values_per_facet=2,
            sort_facet_values_by={"*": "bad"},
        )


async def test_reset_faceting(async_empty_index, default_faceting):
    index = await async_empty_index()
    response = await index.update_faceting(Faceting(max_values_per_facet=17))
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.reset_faceting()
    await async_wait_for_task(index.http_client, response.task_uid)
    response = await index.get_faceting()
    assert response.model_dump() == default_faceting.model_dump()


async def test_str(async_empty_index):
    index = await async_empty_index()
    got = index.__str__()

    assert "uid" in got
    assert "primary_key" in got
    assert "created_at" in got
    assert "updated_at" in got


async def test_repr(async_empty_index):
    index = await async_empty_index()
    got = index.__repr__()

    assert "uid" in got
    assert "primary_key" in got
    assert "created_at" in got
    assert "updated_at" in got


@pytest.mark.usefixtures("indexes_sample")
async def test_delete_if_exists(async_test_client, index_uid):
    assert await async_test_client.get_index(uid=index_uid)
    deleted = await async_test_client.index(index_uid).delete_if_exists()
    assert deleted is True
    with pytest.raises(MeilisearchApiError):
        await async_test_client.get_index(uid=index_uid)


async def test_delete_if_exists_no_delete(async_test_client):
    with pytest.raises(MeilisearchApiError):
        await async_test_client.get_index(uid="none")

    deleted = await async_test_client.index("none").delete_if_exists()
    assert deleted is False


@pytest.mark.usefixtures("indexes_sample")
async def test_delete_if_exists_error(async_test_client, index_uid, monkeypatch):
    def mock_response(*args, **kwargs):
        raise MeilisearchApiError("test", Response(status_code=404))

    monkeypatch.setattr(AsyncHttpRequests, "_send_request", mock_response)
    with pytest.raises(MeilisearchApiError):
        await async_test_client.index(index_uid).delete_if_exists()


@pytest.mark.usefixtures("indexes_sample")
async def test_delete_index_if_exists(async_test_client, index_uid):
    assert await async_test_client.get_index(uid=index_uid)
    deleted = await async_test_client.delete_index_if_exists(index_uid)
    assert deleted is True
    with pytest.raises(MeilisearchApiError):
        await async_test_client.get_index(uid=index_uid)


async def test_delete_index_if_exists_no_delete(async_test_client):
    with pytest.raises(MeilisearchApiError):
        await async_test_client.get_index(uid="none")

    deleted = await async_test_client.delete_index_if_exists("none")
    assert deleted is False


@pytest.mark.usefixtures("indexes_sample")
async def test_delete_index_if_exists_error(async_test_client, index_uid, monkeypatch):
    def mock_response(*args, **kwargs):
        raise MeilisearchApiError("test", Response(status_code=404))

    monkeypatch.setattr(AsyncHttpRequests, "_send_request", mock_response)
    with pytest.raises(MeilisearchApiError):
        await async_test_client.delete_index_if_exists(index_uid)
