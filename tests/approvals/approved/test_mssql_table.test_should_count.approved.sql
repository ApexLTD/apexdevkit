
            EXECUTE AS USER = 'test'
            SELECT count(*) AS n_items
            FROM [test].[apples]
            WHERE pid > 5 AND ([manager] = 5 OR [manager] = 4)
            REVERT
