library ieee, osvvm;
use ieee.numeric_std.all;
use osvvm.CoveragePkg.all;
use osvvm.RandomPkg.all;

entity div_by_3_tb is
end;

architecture testbench of div_by_3_tb is

  signal dividend, quotient: unsigned(31 downto 0);
  constant TEST_INTERVAL: time := 20 ns;
  constant DUV_DELAY: time := 10 ns;

  shared variable dividend_cover_item: CovPType;

begin

  duv: entity work.div_by_3 port map (dividend => dividend, quotient => quotient);

  coverage_collector: process
  begin
    wait on dividend;

    dividend_cover_item.ICover(to_integer(dividend));
  end process;

  stimulus_generator: process
    variable random_variable: RandomPType;
  begin
    dividend_cover_item.AddBins(GenBin(Min => 0, Max => 1_000_000_000, NumBin => 20));

    while not dividend_cover_item.IsCovered loop
      dividend <= to_unsigned(random_variable.RandInt(1_000_000_000), 32);
      wait for TEST_INTERVAL;
    end loop;

    dividend_cover_item.SetMessage("Coverage for dividend input");
    dividend_cover_item.WriteBin(WritePrefix => "OSVVM");
    report("End of simulation. All tests passed.");
    std.env.finish;
  end process;

  response_checker: process
  begin
    wait on dividend;
    wait for DUV_DELAY;

--    assert_eq(quotient, dividend / 3, to_string(to_integer(dividend)) & " / 3 = " & to_string(to_integer(quotient)));
    assert quotient = dividend / 3 report "" severity failure;
  end process;
end;
