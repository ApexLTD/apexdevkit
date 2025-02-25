
            EXECUTE AS USER = 'test'
            DELETE
            FROM [test].[apples]
            WHERE [pid] = test
            REVERT
