library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;

entity gbt_pattern_generator_2_tb is
end entity;

architecture tb_arch of gbt_pattern_generator_2_tb is

    constant CLK_PERIOD : time := 10 ns;
    signal clk   : std_logic := '0';
    signal rst_n : std_logic := '1';

    signal initial_value_i : std_logic_vector(19 downto 0) := (1 downto 0 => '1', others => '0');

    signal tx_data_o : std_logic_vector(83 downto 0);
    signal tx_extra_data_widebus_o : std_logic_vector(31 downto 0);

begin

    clk <= not clk after CLK_PERIOD/2;

    gbt_pattern_generator_0 : entity work.gbt_pattern_generator
    port map (
        clk                      => clk,
        rst_n                    => rst_n,
        initial_value_i          => initial_value_i,
        tx_data_o                => tx_data_o,
        tx_extra_data_widebus_o  => tx_extra_data_widebus_o
    );

    main: process
    begin
        wait for 2 * CLK_PERIOD;

        rst_n <= '1';
        wait for  CLK_PERIOD;
        rst_n <= '0';

        wait for 4 * CLK_PERIOD;

        std.env.finish;

    end process;
end;
