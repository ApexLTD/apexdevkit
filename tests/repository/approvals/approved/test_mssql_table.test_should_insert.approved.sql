
            EXECUTE AS USER = 'test'
            INSERT INTO [test].[apples] (
                [apid], [clr], [pid], [kingdom], [manager]
            )
            VALUES (
                1, red, test, fruits, None
            );
            SELECT
                [apid] AS apid, [clr] AS clr, [pid] AS pid, [kingdom] AS kingdom, [manager] AS manager

                FROM [test].[apples]
                WHERE [apid] = 1 AND ([manager] = 5 OR [manager] = 4)

            REVERT
