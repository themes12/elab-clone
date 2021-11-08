Manual grading
--------------

The system also support questions that require manual grading.  Any
blanks outside the code tags will be treated as blanks for manual
grading.  The format is `{{[`*score*`] `*solution*`}}`.  For example 

    Python is a {{[10] dynamic}} language.

The *score* part is optional.  If omitted, the default value of 1 will be
used.  E.g.,

    Python is a {{dynamic}} language.

Automatically gradable answers
------------------------------

Any manual grading blank with an answer surrounded by ! is treated as an automatically gradable answer.  For example,

    There are {{!8!}} bits in one byte.

Each student submission will be checked against the provided answer.  The full score will be assigned if matched, or zero will be given otherwise.  The automatically assigned score can be changed manually if needed.
