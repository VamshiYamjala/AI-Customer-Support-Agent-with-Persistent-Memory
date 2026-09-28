# Verified SDK Notes

- Date: 2026-09-28
- Hindsight Python Client: `hindsight-client`
- `Hindsight.retain` signature: `(self, bank_id: str, content: str | list[dict[str, typing.Any]], timestamp: datetime.datetime | None = None, context: str | None = None, document_id: str | None = None, metadata: dict[str, str] | None = None, entities: list[dict[str, str]] | None = None, resolve_entities: bool | None = None, tags: list[str] | None = None, update_mode: str | None = None, retain_async: bool = False, operation_id: str | None = None) -> hindsight_client_api.models.retain_response.RetainResponse`
- `Hindsight.recall` signature: `(self, bank_id: str, query: str, types: list[str] | None = None, max_tokens: int = 4096, budget: str = 'mid', trace: bool = False, query_timestamp: str | None = None, include_entities: bool = False, max_entity_tokens: int = 500, include_chunks: bool = False, max_chunk_tokens: int = 8192, include_source_facts: bool = False, max_source_facts_tokens: int = 4096, tags: list[str] | None = None, tags_match: Literal['any', 'all', 'any_strict', 'all_strict', 'exact'] = 'any', tag_groups: list[dict[str, typing.Any]] | None = None, prefer_observations: bool = False, min_scores: dict[str, float] | None = None, temporal_window: dict[str, typing.Any] | None = None) -> hindsight_client_api.models.recall_response.RecallResponse`
- `tags` parameter present in `retain()`: `True`
- `tags` parameter present in `recall()`: `True`
