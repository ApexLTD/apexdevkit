EXECUTE AS USER = 'test'
SELECT
    [apid], [clr]
FROM [test].[apples]
REVERT
