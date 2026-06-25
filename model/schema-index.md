# Schema Index

## Article Schemas

- `articles/artArticle.schema.json`: root union for all articles.
- `articles/artTopic.schema.json`: generic known topic.
- `articles/artConcept.schema.json`: concept article.
- `articles/artHowto.schema.json`: procedure article.
- `articles/artReference.schema.json`: reference article.
- `articles/artTroubleshooting.schema.json`: troubleshooting article.
- `articles/artGlossary.schema.json`: glossary article.
- `articles/artGlossentry.schema.json`: glossary entry article.
- `articles/artOverview.schema.json`: overview specialization.
- `articles/artQuickstart.schema.json`: quickstart specialization.
- `articles/artTutorial.schema.json`: tutorial specialization.
- `articles/artUnknown.schema.json`: unclassified article fallback.

## Shared Contracts

- `articles/sharedArticle.schema.json`: shared article fields.
- `articles/units/unitShared.schema.json`: shared unit fields.
- `articles/units/components/componentShared.schema.json`: shared component fields.
- `articles/units/components/attributes/attributeShared.schema.json`: shared inline attribute fields.

## Dependency Rules

| Parent | Allowed child |
|---|---|
| Article | Unit |
| Unit | Block component |
| `compListOrdered` | `compListItem` |
| `compListUnordered` | `compListItem` |
| `compTable` | `compTableRow` |
| `compTableRow` | `compTableCell` |
| Text-bearing component | Inline attribute |

The dependent schemas exist as named schema files, but validators should not allow them directly inside a unit unless a parent component schema permits them.
