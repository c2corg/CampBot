SELECT * FROM (
    SELECT user_id, count(1) AS contribs, first_contrib FROM (
        SELECT *, written_at AS first_contrib FROM contribution
        WHERE type!="i" AND written_at < "2018-05-20"
        GROUP BY document_id, user_id
    )
    GROUP BY user_id
    ORDER BY contribs DESC
)
WHERE contribs >= 5