
            EXECUTE AS USER = 'test'
            SELECT count(*) AS n_items
            FROM [test].[apples]
            WHERE ([manager] = 5 OR [manager] = 4)
            REVERT
