
            EXECUTE AS USER = 'test'
            SELECT
                [apid], [clr], [pid]
            FROM [test].[apples]
            WHERE [pid] = test AND [apid] = 1
            REVERT
