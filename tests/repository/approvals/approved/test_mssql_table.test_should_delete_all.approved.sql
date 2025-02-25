
            EXECUTE AS USER = 'test'
            DELETE
            FROM [test].[apples]
            WHERE ([manager] = 5 OR [manager] = 4)
            REVERT
