
            EXECUTE AS USER = 'John'
            SELECT COUNT(item_name) AS name_count
            FROM TABLE
            WHERE (([item_id] LIKE N'begin%') OR ([item_name] LIKE N'%end'))


