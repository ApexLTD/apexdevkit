
            EXECUTE AS USER = 'test'
            INSERT INTO [test].[apples] (
                [apid], [clr], [pid]
            )
            VALUES (
                1, red, test
            );
            SELECT
                [apid] AS apid, [clr] AS clr, [pid] AS pid

                FROM [test].[apples]
                WHERE [pid] = test AND [apid] = 1

            REVERT
