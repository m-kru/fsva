library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;

entity gbt_pattern_generator is
  port (
    clk                     : in  std_logic;
    rst_n                   : in  std_logic;
    initial_value_i         : in  std_logic_vector(19 downto 0);
    tx_data_o               : out std_logic_vector(83 downto 0);
    tx_extra_data_widebus_o : out std_logic_vector(31 downto 0)
  );
end gbt_pattern_generator;

architecture behavioral of gbt_pattern_generator is

begin

  process(clk)
    variable sc_ec_word_cnt   : unsigned( 1 downto 0);
    variable common_word_cnt  : unsigned(19 downto 0);
    variable widebus_word_cnt : unsigned(15 downto 0);
  begin
    if rising_edge(clk) then
      if rst_n = '0' then
        sc_ec_word_cnt      := unsigned(initial_value_i(sc_ec_word_cnt'range));
        common_word_cnt     := unsigned(initial_value_i(common_word_cnt'range));
        widebus_word_cnt    := unsigned(initial_value_i(widebus_word_cnt'range));
        tx_data_o               <= (others => '0');
        tx_extra_data_widebus_o <= (others => '0');
      else
        -- Comment: The patter is constant "11" in order to reset the SC FSM of the GBTx ASIC.
        tx_data_o(83 downto 82) <= "11";

        -- External Control (SC-EC) cnt pattern generation:
        -------------------------------------------------------
        tx_data_o(81 downto 80) <= std_logic_vector(sc_ec_word_cnt);
        sc_ec_word_cnt := sc_ec_word_cnt + 1;

        -- Common data cnt pattern generation:
        ------------------------------------------
        for i in 0 to 3 loop
            tx_data_o((20*i)+19 downto (20*i)) <= std_logic_vector(common_word_cnt);
        end loop;
        common_word_cnt := common_word_cnt + 1;

        -- Wide-Bus extra data cnt pattern generation:
        --------------------------------------------------
        for i in 0 to 1 loop
            tx_extra_data_widebus_o((16*i)+15 downto (16*i)) <= std_logic_vector(widebus_word_cnt);
        end loop;
        widebus_word_cnt := widebus_word_cnt + 1;

      end if;
    end if;
  end process;

end behavioral;
