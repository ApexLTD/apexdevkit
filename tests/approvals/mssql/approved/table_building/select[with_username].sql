EXECUTE AS USER = 'test'
SELECT
    [apid], [clr]
FROM [test].[apples]
WHERE [apid] = 1
REVERT
