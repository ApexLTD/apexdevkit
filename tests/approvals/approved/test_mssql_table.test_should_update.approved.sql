
            EXECUTE AS USER = 'test'
            UPDATE [test].[apples]
            SET
                clr = red, pid = test, kingdom = fruits, manager = None
            WHERE [apid] = 1 AND pid > 5 AND ([manager] = 5 OR [manager] = 4)
            REVERT
