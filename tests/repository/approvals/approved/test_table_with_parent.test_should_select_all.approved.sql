
            EXECUTE AS USER = 'test'
            SELECT
                [apid], [clr], [pid]
            FROM [test].[apples]
            WHERE [pid] = test
            ORDER BY apid
            REVERT
