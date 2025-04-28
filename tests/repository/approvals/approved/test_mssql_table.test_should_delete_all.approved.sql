
            EXECUTE AS USER = 'test'
            DELETE
            FROM [test].[apples]
            WHERE pid > 5 AND ([manager] = 5 OR [manager] = 4)
            REVERT
