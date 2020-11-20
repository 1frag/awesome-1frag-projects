create table app_answer (
   id serial primary key,
   first int not null,
   op varchar(3) not null,
   second int not null,
   answer text,
   res bool not null,
   created_at timestamp default now()
);

create or replace function calc(
    a int,
    op varchar(3),
    b int
) returns int as $$
begin
    if op = '/' then
        return a / b;
    else
        return a * b;
    end if;
end;
$$ language plpgsql;

create or replace function css_class(
    cor bool
) returns text as $$
begin
    if cor then
        return 'success';
    else
        return 'danger';
    end if;
end;
$$ language plpgsql;

create table app_settings (
    key text primary key,
    value text not null
);
insert into app_settings
values ('mt_for_first', '[2,3,4,5,6,7,8,9]'),
       ('mt_for_second', '[2,3,4,5,6,7,8,9]');
