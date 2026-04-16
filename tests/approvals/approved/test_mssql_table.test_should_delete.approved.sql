
            EXECUTE AS USER = 'test'
            DELETE
            FROM [test].[apples]
            WHERE [apid] = 1 AND pid > 5 AND ([manager] = 5 OR [manager] = 4)
            REVERT
