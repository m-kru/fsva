library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity div_by_3 is
  port (
    dividend: in unsigned(31 downto 0);
    quotient: out unsigned(31 downto 0)
  );
end div_by_3;

architecture comb of div_by_3 is
begin

  process (dividend) is
    variable d, q, r: unsigned(31 downto 0);
  begin
    d := dividend;

    q := (d srl 2) + (d srl 4);
    q := q + (q srl 4);
    q := q + (q srl 8);
    q := q + (q srl 16);
    r := resize(d - q * 3, 32);
    q := resize(q +(5 * (r+1) srl 4), 32);

    quotient <= q;
  end process;

end comb;
