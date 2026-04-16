
            EXECUTE AS USER = 'test'
            DELETE
            FROM [test].[apples]
            WHERE [pid] = test AND [apid] = 1
            REVERT
