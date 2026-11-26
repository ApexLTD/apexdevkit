INSERT INTO [test].[apples] (
    [apid], [clr]
)
VALUES (
    1, red
);
SELECT
    [apid] AS apid, [clr] AS clr
    FROM [test].[apples]
    WHERE [apid] = 1
REVERT
