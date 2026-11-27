EXECUTE AS USER = 'test'
DELETE
FROM [test].[apples]
WHERE [apid] = 1
REVERT
