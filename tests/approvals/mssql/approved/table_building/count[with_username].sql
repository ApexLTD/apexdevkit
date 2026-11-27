EXECUTE AS USER = 'test'
SELECT count(*) AS n_items
FROM [test].[apples]
REVERT
