
            EXECUTE AS USER = 'test'
            UPDATE [test].[apples]
            SET
                clr = red
            WHERE [pid] = test AND [apid] = 1
            REVERT
