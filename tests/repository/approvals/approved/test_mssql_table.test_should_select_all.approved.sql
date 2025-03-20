
            EXECUTE AS USER = 'test'
            SELECT
                [apid], [clr], [pid], [kingdom], [manager]
            FROM [test].[apples]
            WHERE ([manager] = 5 OR [manager] = 4)
            ORDER BY apid DESC
            REVERT
